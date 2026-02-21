import html
import os
import re
import string
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import Tag, BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

from config import User_Agent


def get_request(url: str):
    # Добавляем хэдер, чтобы соблюсти Wikimedia Foundation User-Agent Policy
    headers = {'User-Agent': User_Agent}
    return requests.get(url, headers=headers, allow_redirects=True)


def get_url_by_tag(url, tag):
    netloc = urlparse(url).netloc
    if netloc == 'web.archive.org':
        # Ищем последнюю архивную версию вместо определённой даты, например:
        # https://web.archive.org/web/20240619223918/... ---> https://web.archive.org/web/2/...
        return netloc, 'https://' + netloc + '/web/2/' + tag['href'].split('/', 3)[3]
    else:
        return netloc, 'https://' + netloc + tag['href']


def is_hidden(tag):
    """
    Проверяет, скрыт ли тег.
    - через style display:none
    - через aria-hidden
    - через class noprint или hidden
    """
    if not isinstance(tag, Tag):
        return False
    if tag.has_attr('style') and 'display:none' in tag['style'].replace(" ", "").lower():
        return True
    if tag.has_attr('aria-hidden') and tag['aria-hidden'].lower() == 'true':
        return True
    if tag.has_attr('hidden'):
        return True
    classes = tag.get('class', '')
    return any(c.lower() in ['noprint', 'hidden'] for c in classes)


def get_paragraphs(soup: BeautifulSoup) -> list[str]:
    paragraphs = [p.get_text().strip() for p in soup.select(':scope > * > p')]
    if len(paragraphs) > 0:
        return paragraphs
    paragraphs = [p.get_text().strip() for p in soup.select(':scope > p')]  # 20240321 case (hosted on web.archive.org)
    if len(paragraphs) > 0:
        return paragraphs
    return [soup.get_text().strip()]  # 20260221 case (en.wikipedia.org main page hosted on web.archive.org)


def clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    for el in soup:
        if is_hidden(el):
            el.decompose()
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
            # INLINE-режим
            target_cell = cell
        else:
            # TABLE-режим
            target_cell = cell.find_next(next_tags)
            if not target_cell:
                continue

        parts = []
        extract_info(target_cell, parts)
        value = ' '.join(parts).strip()

        if value:
            results.append(value)

    return '; '.join(results) if results else None


def remove_brackets(text: str) -> str:
    """Убирает из текста примечания, написанные в квадратных скобках"""
    res = []
    depth = 0
    for ch in text:
        if ch == "[":
            depth += 1
        elif ch == "]":
            if depth > 0:
                depth -= 1
        else:
            if depth == 0:
                res.append(ch)
    return " ".join("".join(res).split())


def html_to_text(html: str) -> str:
    depth = 0
    parts = []
    prev = 0
    for i in range(len(html)):
        if html[i] == "<":
            depth += 1
            if depth == 1:
                parts.append(html[prev:i])
        elif html[i] == ">":
            depth -= 1
            if depth == 0:
                prev = i + 1
    parts.append(html[prev:])
    return ''.join(parts)


def replace_links_with_numbers(html: str) -> str:
    """Заменяет ссылки в тексте (но не в тегах) на числа"""
    counter = 0
    links_map = {}
    depth = 0
    prefix = 'https://'
    parts = []
    stop_chars = string.whitespace + '"()[]{}<>,!'

    prev, i = 0, 0
    while i < len(html):
        if html[i] == "<":
            depth += 1
        elif html[i] == ">":
            depth -= 1
        if depth == 0 and html.startswith(prefix, i):
            parts.append(html[prev:i])
            end = i + len(prefix)
            while end < len(html) and html[end] not in stop_chars:
                end += 1
            link = html[i:end]
            if link not in links_map:
                counter += 1
                links_map[link] = f'[{counter}]'
            parts.append(links_map[link])
            prev, i = end, end
        else:
            i += 1
    parts.append(html[prev:])
    return ''.join(parts)


def read_last_article(last_article_file):
    # Читаем название последней статьи из файла
    if not os.path.exists(last_article_file):
        return ''
    with open(last_article_file, 'r', encoding='utf-8') as file:
        return file.read().strip()


def write_last_article(title, last_article_file):
    # Записываем последнюю статью в файл
    with open(last_article_file, 'w', encoding='utf-8') as file:
        file.write(title)


def visible_length(html_text: str) -> int:
    text = re.sub(r'<[^>]+>', '', html_text)
    text = html.unescape(text)
    return len(text)


def draw_centered_text(
        text: str,
        font_path: str = "Renju.otf",
        image_size: int = 2000,
        margin: int = 100,
        max_lines: int = 5,
        start_font_size: int = 120,
        min_font_size: int = 20,
        line_spacing: int = 10,
) -> Optional[Image.Image]:
    """
    Рисует текст по центру картинки image_size x image_size.
    Автоматически переносит текст на N строк (<= max_lines).
    Если не влезает — уменьшает размер шрифта.
    """

    img = Image.new("RGB", (image_size, image_size), "white")
    draw = ImageDraw.Draw(img)

    max_width = image_size - 2 * margin
    max_height = image_size - 2 * margin

    words = text.split()

    def text_width(txt: str, _font):
        bbox = draw.textbbox((0, 0), txt, font=_font)
        return bbox[2] - bbox[0]

    def layout_lines(_font):
        _lines = []
        current = ""

        for word in words:
            test = word if not current else current + " " + word
            if text_width(test, _font) <= max_width:
                current = test
            else:
                _lines.append(current)
                current = word

        if current:
            _lines.append(current)

        return _lines

    font_size = start_font_size

    while font_size >= min_font_size:
        font = ImageFont.truetype(font_path, font_size)
        lines = layout_lines(font)

        line_height = font.getbbox("Hg")[3]
        total_height = len(lines) * line_height + (len(lines) - 1) * line_spacing

        if len(lines) <= max_lines and total_height <= max_height:
            break

        font_size -= 2
    else:
        print("Текст не помещается даже с минимальным размером шрифта")
        return None

    block_width = max(text_width(line, font) for line in lines)
    x = (image_size - block_width) // 2
    y = (image_size - total_height) // 2

    cy = y
    for line in lines:
        lw = text_width(line, font)
        draw.text(
            (x + (block_width - lw) // 2, cy),
            line,
            fill="black",
            font=font,
        )
        cy += line_height + line_spacing

    return img
