import html
import os
import re
from urllib.parse import urlparse

import requests
from bs4 import Tag

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


def clean_soup(soup):
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


def extract_attrs_id_info(soup, attrs_id):
    results = []

    # Получаем все элементы с нужным id
    cells = soup.find_all(attrs={'id': attrs_id})
    for cell in cells:
        next_cell = cell.find_next(['td', 'th'])
        if next_cell:
            parts = []
            extract_info(next_cell, parts)
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
