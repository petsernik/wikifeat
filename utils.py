import copy
import html
import re
import string
from datetime import datetime, UTC
from io import BytesIO
from typing import Optional
from urllib.parse import urlparse, unquote, quote, parse_qs

import requests
from PIL import Image, ImageDraw, ImageFont
from bs4 import Tag, BeautifulSoup
from bs4.element import PageElement, NavigableString
from requests import Response

from constants import User_Agent, FONT_PATH
from i18n import TRANSLATIONS
from models import ArticleContext, ParagraphResult


# Добавляем хэдер, чтобы соблюсти Wikimedia Foundation User-Agent Policy
def get_request(url: str) -> Response:
    headers = {'User-Agent': User_Agent}
    return requests.get(url, headers=headers, allow_redirects=True)


def unquote_url(url: str) -> str:
    return unquote(url)


def quote_url(url: str) -> str:
    return quote(unquote(url), safe=":/")


def get_quote_url_by_str(lang: str, url_or_title: str) -> str:
    if url_or_title.startswith('https://'):
        return quote_url(url_or_title)
    title = url_or_title.replace(' ', '_')
    return quote_url(f'https://{lang}.wikipedia.org/wiki/{title}')


def get_title_by_url(url: str) -> str:
    url = unquote_url(join_url('en.wikipedia.org', url))

    if not url.startswith("http"):
        return url.replace("_", " ")

    parsed = urlparse(url)
    path = parsed.path

    if "/wiki/" in path:
        title = path.split("/wiki/", 1)[1]
    else:
        title = path.lstrip("/")

    title = title.split("#")[0].split("?")[0]

    return title.replace("_", " ")


def get_quote_url_by_context(ctx: ArticleContext) -> str:
    return get_quote_url_by_str(ctx.lang, ctx.url_or_title)


def get_quote_url_by_tag(netloc: str, tag: Tag) -> str:
    url = tag.get("href") or tag.get("resource")
    if not url:
        url = tag.parent.get("href") if tag.parent else ""
    return quote_url(join_url(netloc, url)) if url else ""


def split_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    return parsed.netloc, parsed.path


def join_url(netloc: str, path: str) -> str:
    if path.startswith('//'):
        return f'https:{path}'
    if path.startswith('https://'):
        return path
    if netloc == 'web.archive.org':
        # Ищем последнюю архивную версию вместо определённой даты, например:
        # https://web.archive.org/web/20240619223918/... ---> https://web.archive.org/web/2/...
        return f'https://{netloc}/web/2/{path.split('/', 3)[3]}'
    else:
        return f'https://{netloc}{path}'


def has_link(html_code: str) -> bool:
    if not html_code:
        return False
    soup = BeautifulSoup(html_code, 'html.parser')
    return soup.find('a', href=True) is not None


def clean_select_list(soup: PageElement | Tag | NavigableString | None | int, selector: str) -> list[str]:
    return [q for p in soup.select(selector) if (q := p.get_text().strip())]


def get_paragraphs(
        soup: PageElement | Tag | NavigableString | None | int
) -> ParagraphResult:
    paragraphs = clean_select_list(soup, ':scope > * > p')

    if not paragraphs:
        paragraphs = clean_select_list(soup, ':scope > p')

    if not paragraphs:
        paragraphs = clean_select_list(soup, 'p')

    result = ParagraphResult(paragraphs=paragraphs)

    if soup and isinstance(soup, (Tag, PageElement)):
        disambig = soup.select_one('div.ts-disambig')

        if disambig:
            result.is_disambig = True

            for a in soup.select('a[rel="mw:WikiLink"]'):
                href = a.get('href')

                if not href:
                    continue

                query = parse_qs(urlparse(href).query)

                if query.get('redlink') == ['1']:
                    continue

                result.titles.append(get_title_by_url(href))

    return result


def _attr_list(tag: Tag, attr: str) -> list[str]:
    val = tag.get(attr)

    if isinstance(val, str):
        return val.lower().split()
    if isinstance(val, (list, tuple)):
        return [v.lower() for v in val if isinstance(v, str)]

    return []


def is_hidden(tag: Tag) -> bool:
    # style="display:none"
    style = tag.get("style", "").replace(" ", "").lower()
    if "display:none" in style:
        return True

    # hidden attribute
    if tag.has_attr("hidden"):
        return True

    # role
    if {"note", "presentation"} & set(_attr_list(tag, "role")):
        return True

    # классы
    if ({"noprint", "hidden", "metadata", "infobox-above", "ts-doc-footer", "ts-doc-doc"}
            & set(_attr_list(tag, "class"))):
        return True

    return False


def clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    for tag in soup.find_all(True):
        if not tag.decomposed and is_hidden(tag):
            tag.decompose()

    for table in soup.find_all('table'):
        if table.decomposed:
            continue

        img = table.select_one('a[href] img')

        if img and img.parent and img.parent.name == 'a':
            table.replace_with(copy.copy(img.parent))
        else:
            table.decompose()

    return soup


def filter_soup(soup: BeautifulSoup, *, remove_kwargs) -> BeautifulSoup:
    for tag in soup.find_all(attrs=remove_kwargs):
        if not tag.decomposed:
            tag.decompose()
    return soup


def extract_info(node, parts):
    for elem in node.children:
        if isinstance(elem, str):
            text = elem.strip()
            if text:
                parts.append(text)
        elif is_hidden(elem):
            continue
        elif elem.name == 'a' and elem.has_attr('href'):
            href = elem['href']
            if href.startswith('//'):
                href = 'https:' + href
            text = elem.get_text(strip=True)
            if text:
                parts.append(f"<a href='{href}'>{text}</a>")
        elif 'vcard' in (elem.get('class') or []):
            # Особая обработка для vcard — достаём <span class="fn" id="creator">
            creator = elem.find('span', class_='fn', id='creator')
            if creator:
                link = creator.find('a', href=True)
                if link:
                    href = link['href']
                    if href.startswith('//'):
                        href = 'https:' + href
                    text = link.get_text(strip=True)
                    if text:
                        parts.append(f"<a href='{href}'>{text}</a>")
                else:
                    text = creator.get_text(strip=True)
                    if text:
                        parts.append(text)
        else:
            # Рекурсивно обходим другие теги
            extract_info(elem, parts)


def extract_attrs_info(soup, *, find_kwargs, next_tags):
    """
    Универсальное извлечение текстовой/HTML-информации из таблиц MediaWiki по произвольным HTML-атрибутам.

    Функция:
    1. Ищет все элементы, подходящие под ``find_kwargs``.
    2. Выбирает ячейки следующие непосредственно после каждого из next_tags в элементах (если None, то выбираются все ячейки).
    3. Извлекает содержимое выбранных ячеек через ``extract_info``.
    4. Объединяет результаты через ``; ``.

    :param soup:
        Объект BeautifulSoup с разобранным HTML-документом.
    :type soup: bs4.BeautifulSoup

    :param find_kwargs:
        Критерии поиска для ``BeautifulSoup.find_all``.
        Передаются как словарь атрибутов HTML.

        Примеры:
            {'id': 'fileinfotpl_aut'}
            {'class': 'licensetpl_attr'}
            {'data-source': 'author'}

    :type find_kwargs: dict[str, str]

    :param next_tags:
        Имена HTML-тегов, которые считаются ячейкой со значением в следующей за ними ячейке,
        используются в ``find_next``.

    :type next_tags: tuple[str, ...] | None

    :return:
        Объединённая строка с найденными значениями или ``None``,
        если данные не найдены.
    :rtype: str | None
    """
    results = []

    cells = soup.find_all(attrs=find_kwargs)
    for cell in cells:
        if next_tags is None:
            target_cell = cell
        else:
            target_cell = cell.find_next(next_tags)
            if not target_cell:
                continue

        descriptions = target_cell.find_all('div', class_='description', recursive=False)
        if descriptions:
            selected = None

            for d in descriptions:
                if 'ru' in (d.get('class') or []):
                    selected = d
                    break

            if not selected:
                for d in descriptions:
                    if 'en' in (d.get('class') or []):
                        selected = d
                        break

            if not selected:
                selected = descriptions[0]

            lang_label = selected.find('span', class_='language')
            if lang_label:
                lang_label.decompose()

            parts = []
            extract_info(selected, parts)
        else:
            parts = []
            extract_info(target_cell, parts)

        value = ' '.join(parts).strip()
        if value:
            results.append(value)

    results = list(sorted(set(results)))  # unique
    return '; '.join(results) if results else None


def remove_brackets_except_letters_only_case(text: str) -> str:
    """Удаляет [...] если внутри есть цифры или вложенные скобки."""
    res = []

    depth = 0
    buf = []
    remove_current = False

    for ch in text:
        if ch == "[":
            if depth == 0:
                buf = ["["]
                remove_current = False
            else:
                remove_current = True
                buf.append(ch)

            depth += 1

        elif ch == "]":
            if depth > 0:
                depth -= 1
                buf.append(ch)

                if depth == 0:
                    if not remove_current:
                        res.extend(buf)
            else:
                res.append(ch)

        elif depth > 0:
            if ch.isdigit():
                remove_current = True

            buf.append(ch)

        else:
            res.append(ch)

    return " ".join("".join(res).split())


def html_to_text(html_code: str) -> str:
    depth = 0
    parts = []
    prev = 0
    for i in range(len(html_code)):
        if html_code[i] == "<":
            depth += 1
            if depth == 1:
                parts.append(html_code[prev:i])
        elif html_code[i] == ">":
            depth -= 1
            if depth == 0:
                prev = i + 1
    parts.append(html_code[prev:])
    return ''.join(parts)


def update_links(netloc: str, html_code: str) -> str:
    soup = BeautifulSoup(html_code, 'html.parser')

    langs = set(TRANSLATIONS.keys())

    for a in soup.find_all('a', href=True):
        href = join_url(netloc, a['href'])

        # https://en.wikipedia.org/wiki/ru:Статья
        # -> https://ru.wikipedia.org/wiki/Статья
        if href.startswith('https://en.wikipedia.org/wiki/'):
            title = href.removeprefix('https://en.wikipedia.org/wiki/')

            for lang in langs:
                prefix = f'{lang}:'
                if title.startswith(prefix):
                    href = f'https://{lang}.wikipedia.org/wiki/{title[len(prefix):]}'
                    break

        a['href'] = quote_url(href)

    return str(soup)


def replace_links_with_numbers(html_code: str) -> str:
    """Заменяет ссылки в тексте (но не в тегах) на числа"""
    counter = 0
    links_map = {}
    depth = 0
    prefix = 'https://'
    parts = []
    stop_chars = string.whitespace + '"()[]{}<>,!'

    prev, i = 0, 0
    while i < len(html_code):
        if html_code[i] == "<":
            depth += 1
        elif html_code[i] == ">":
            depth -= 1
        if depth == 0 and html_code.startswith(prefix, i):
            parts.append(html_code[prev:i])
            end = i + len(prefix)
            while end < len(html_code) and html_code[end] not in stop_chars:
                end += 1
            link = html_code[i:end]
            if link not in links_map:
                counter += 1
                links_map[link] = f'[{counter}]'
            parts.append(links_map[link])
            prev, i = end, end
        else:
            i += 1
    parts.append(html_code[prev:])
    return ''.join(parts)


def visible_length(html_text: str) -> int:
    text = re.sub(r'<[^>]+>', '', html_text)
    text = html.unescape(text)
    return len(text)


def get_img_buf_by_text(text: str):
    img = draw_centered_text(text)
    if not img:
        return None

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def draw_centered_text(
        text: str,
        font_path: str = FONT_PATH,
        max_side: int = 1500,
        max_ratio: float = 10,
        margin: int = 80,
        start_font: int = 120,
        min_font: int = 20,
        line_spacing: int = 10,
) -> Optional[Image.Image]:
    words = text.split()

    def wrap(font, max_w):
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))

        def w(s: str) -> float:
            b = draw.textbbox((0, 0), s, font=font)
            return b[2] - b[0]

        lines, cur = [], ""
        for word in words:
            test = word if not cur else cur + " " + word
            if w(test) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)

        return lines, w

    for font_size in range(start_font, min_font - 1, -2):
        font = ImageFont.truetype(font_path, font_size)

        max_w_guess = max_side - 2 * margin
        lines, _ = wrap(font, max_w_guess)

        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))

        line_h = font.getbbox("Hg")[3]

        text_w = max(
            draw.textbbox((0, 0), line, font=font)[2]
            for line in lines
        )
        text_h = len(lines) * line_h + (len(lines) - 1) * line_spacing

        w = int(min(text_w + 2 * margin, max_side))
        h = int(min(text_h + 2 * margin, max_side))

        if max(w, h) / min(w, h) <= max_ratio:
            break
    else:
        return None

    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    y = int((h - text_h) / 2)

    for line in lines:
        lw = draw.textbbox((0, 0), line, font=font)[2]
        draw.text(
            ((w - lw) // 2, y),
            line,
            font=font,
            fill="black",
        )
        y += line_h + line_spacing

    return img


def ends_with_one_char_abbr(t: str) -> bool:
    if len(t) == 0:
        return False
    if len(t) == 1:
        return t.isupper() and t.isalpha()
    if not t[-2].isspace() and t[-2].isalpha():
        return False
    return t[-1].isupper() and t[-1].isalpha()


def is_balanced(s: str) -> tuple[bool, int]:
    closing = {")": "(", "»": "«", "“": "„"}  # "}": "{", "]": "[", "\"": "\""
    opening = set(closing.values())

    stack = []

    for i, char in enumerate(s):
        if char in opening:
            stack.append((i, char))
        elif char in closing:
            if not stack:
                return False, i
            if stack[-1][1] != closing[char]:
                return False, stack[0][0]
            stack.pop()

    if stack:
        return False, stack[0][0]

    return True, -1


def get_today():
    return datetime.now(UTC).strftime("%Y-%m-%d")


def normalize_lang(code: str | None):
    if not code:
        return "en"
    base = code.lower().split("-")[0]
    return base if base in TRANSLATIONS.keys() else "en"
