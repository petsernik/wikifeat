import io
import os
import re
import sys
import requests
from urllib.parse import urlparse
import telebot
from bs4 import BeautifulSoup
from config import Config

# stdout/stderr → UTF-8 для корректной кириллицы
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# получаем токен из переменной окружения
TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_request(url: str):
    # Добавляем хэдер, чтобы соблюсти Wikimedia Foundation User-Agent Policy
    headers = {'User-Agent': 'wikifeat/0.1 (https://github.com/petsernik/wikifeat)'}
    return requests.get(url, headers=headers, allow_redirects=True)


def get_url_by_tag(url, tag):
    netloc = urlparse(url).netloc
    if netloc == 'web.archive.org':
        # Ищем последнюю архивную версию вместо определённой даты, например:
        # https://web.archive.org/web/20240619223918/... ---> https://web.archive.org/web/2/...
        return netloc, 'https://' + netloc + '/web/2/' + tag['href'].split('/', 3)[3]
    else:
        return netloc, 'https://' + netloc + tag['href']


def get_image_parameters(url, img_tag):
    init = None, [], None, None
    if not (img_tag and img_tag.has_attr('src') and img_tag.parent.has_attr('href')):
        return init

    image_url, image_licenses, image_page_url, author_html = init
    netloc, image_page_url = get_url_by_tag(url, img_tag.parent)
    response = get_request(image_page_url)
    if response.status_code in (404, 429):
        return init
    if response.status_code != 200:
        raise Exception(f'Unexpected response code when get image page: {response.status_code}\n'
                        f'Response body: {response.content}')

    image_soup = BeautifulSoup(response.text, 'html.parser')

    # Подбираем разрешение не больше 2500×2500
    width_max, height_max = 2500, 2500
    resolutions_span = image_soup.find('span', class_='mw-filepage-other-resolutions')
    if resolutions_span:
        links = resolutions_span.find_all('a', href=True)
        for link in links[::-1]:
            match = re.search(r'(\d+)\s*[×x]\s*(\d+)', link.text)
            if match:
                width, height = int(match.group(1)), int(match.group(2))
                if width <= width_max and height <= height_max:
                    image_url = 'https:' + link['href']
                    break
    else:
        file_link_tag = image_soup.find('a', class_='internal')
        if file_link_tag and file_link_tag.has_attr('href'):
            image_url = 'https:' + file_link_tag['href']

    # Собираем лицензии
    license_tags = image_soup.find_all(class_=re.compile('licensetpl_short'))
    for tag in license_tags:
        clean_text = re.sub(r'\s+', ' ', tag.get_text(strip=True)).strip()
        image_licenses.append(clean_text)

    image_licenses = list(set(image_licenses))

    if netloc == 'web.archive.org' and image_url:
        lst = image_url.split('https://')
        lst[1] = lst[1][:-1] + 'if_/'
        image_url = 'https://'.join(lst)

    # Получаем автора (в виде HTML, совместимого с Telegram Bot API)
    author_html = None
    author_cell = image_soup.find(attrs={'id': 'fileinfotpl_aut'})
    if author_cell:
        value_cell = author_cell.find_next(['td', 'th'])
        if value_cell:
            parts = []
            for elem in value_cell.children:
                if isinstance(elem, str):
                    text = elem.strip()
                    if text:
                        parts.append(text)
                elif elem.name == 'a' and elem.has_attr('href'):
                    href = elem['href']
                    if href.startswith('//'):
                        href = 'https:' + href
                    parts.append(f"<a href='{href}'>{elem.get_text(strip=True)}</a>")
            author_html = ' '.join(parts).strip()

    # Получаем источник, если автор неизвестен
    if not author_html or 'неизвест' in author_html.lower():
        source_cell = image_soup.find(attrs={'id': 'fileinfotpl_src'})
        if source_cell:
            value_cell = source_cell.find_next(['td', 'th'])
            if value_cell:
                parts = []
                for elem in value_cell.children:
                    if isinstance(elem, str):
                        text = elem.strip()
                        if text:
                            parts.append(text)
                    elif elem.name == 'a' and elem.has_attr('href'):
                        href = elem['href']
                        if href.startswith('//'):
                            href = 'https:' + href
                        parts.append(f"<a href='{href}'>{elem.get_text(strip=True)}</a>")
                author_html = ' '.join(parts).strip() or 'неизвестен'

    return image_url, image_licenses, image_page_url, author_html


def clean_soup(soup):
    for el in soup.select('[style*="display:none"], .noprint, [aria-hidden="true"], [hidden]'):
        el.decompose()
    return soup


def get_featured_article(wiki_url):
    # Загружаем HTML
    response = get_request(wiki_url)
    if response.status_code != 200:
        raise Exception(f'Unexpected response code when get wiki page: {response.status_code}\n'
                        f'Response body: {response.content}')
    response.encoding = 'utf-8'
    soup = clean_soup(BeautifulSoup(response.text, 'html.parser'))

    # Определяем блок с избранной статьёй
    featured_block = soup.find('div', id='main-tfa' if '/Заглавная_страница' in wiki_url else 'mw-content-text')
    paragraphs = [p.get_text().strip() for p in featured_block.find_all('p')]
    link_tag = featured_block.find('a', href=True)
    title = link_tag['title'] if '/Заглавная_страница' in wiki_url else wiki_url.split('/')[-1]
    _, article_link = get_url_by_tag(wiki_url, link_tag)
    img_tag = featured_block.find('img')

    image_url, image_licenses, image_page_url, author_html = get_image_parameters(wiki_url, img_tag)

    return title, paragraphs, image_url, article_link, image_licenses, image_page_url, author_html


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


def get_trimmed_text(paragraphs, max_length):
    total_length, text = 0, ''
    for paragraph in paragraphs:
        paragraph = remove_brackets(paragraph)
        paragraph_length = len(paragraph) + 2
        text += paragraph
        if total_length + paragraph_length > max_length:
            t = str(text[:max_length].rsplit('.', 1)[0])
            # режем дальше, если обрезали на аббревиатуре/инициале
            while len(t) > 1 and t[-2].isspace() and t[-1].upper() == t[-1]:
                t = str(t.rsplit('.', 1)[0])
            return t + '.\n\n'
        text += '\n\n'
        total_length += paragraph_length
    return text


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


def visible_length(html_text):
    """Возвращает длину видимого текста (без HTML-тегов)."""
    return len(BeautifulSoup(html_text, "html.parser").get_text())


def send_to_telegram(title, paragraphs, image_url, link, image_licenses, image_page_url,
                     author_html, telegram_channels, rules_url):
    caption_beginning = f"<b>{title}</b>\n\n"
    caption_end = (
        f"<a href='{link}'>Читать статью</a>\n\n"
        f"<a href='{rules_url}'>Лицензия на текст: CC BY-SA</a>\n"
    )

    # Дополняем caption_end, вычисляем максимальную длину под остальной текст
    if image_url:
        # Добавляем лицензии
        if "Public domain" in image_licenses or "PDM" in image_licenses:
            caption_end += f"<a href='{image_page_url}'>Лицензия на изображение: Общественное достояние</a>"
        elif "CC0" in image_licenses:
            caption_end += f"<a href='{image_page_url}'>Лицензия на изображение: CC0</a>"
        else:
            if len(image_licenses) == 1:
                caption_end += f"<a href='{image_page_url}'>Лицензия на изображение: {image_licenses[0]}</a>"
            else:
                caption_end += (f"<a href='{image_page_url}'>Лицензии на изображение: "
                                + ", ".join(image_licenses) + "</a>")
            # Добавляем автора
            if author_html:
                caption_end += f" (автор: {author_html})"

        max_text_len = 1024 - visible_length(caption_beginning) - visible_length(caption_end)
    else:
        max_text_len = 4096 - visible_length(caption_beginning) - visible_length(caption_end)

    # Формируем подпись и отправляем сообщение в каждый канал
    caption = caption_beginning + get_trimmed_text(paragraphs, max_text_len) + caption_end
    if image_url:
        for channel in telegram_channels:
            bot.send_photo(channel, image_url, caption=caption, parse_mode='HTML')
    else:
        for channel in telegram_channels:
            bot.send_message(channel, caption, parse_mode='HTML')


def main(config: Config):
    title, paragraphs, image_url, link, image_licenses, image_page_url, author_html = get_featured_article(
        config.WIKI_URL)
    last_title = read_last_article(config.LAST_ARTICLE_FILE)

    if title != last_title:
        send_to_telegram(title, paragraphs, image_url, link, image_licenses, image_page_url,
                         author_html, config.TELEGRAM_CHANNELS, config.RULES_URL)
        write_last_article(title, config.LAST_ARTICLE_FILE)
        print(f'Избрана новая статья: {title}')
    else:
        print('Избранная статья не изменилась')
