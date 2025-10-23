import io
import os
import re
import sys
from typing import Optional

import telebot
from bs4 import BeautifulSoup
from config import Config
from models import Article, Image
from utils import (
    get_request,
    get_url_by_tag,
    clean_soup,
    remove_brackets,
    read_last_article,
    write_last_article,
    visible_length,
    extract_from_next,
)

# stdout/stderr → UTF-8 для корректной кириллицы
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# получаем токен из переменной окружения
TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_image_by_src(url, img_tag) -> Optional[Image]:
    if not (img_tag and img_tag.has_attr('src') and img_tag.parent.has_attr('href')):
        return None

    netloc, image_page_url = get_url_by_tag(url, img_tag.parent)
    response = get_request(image_page_url)
    if response.status_code in (404, 429):
        return None
    if response.status_code != 200:
        raise Exception(f'Unexpected response code when get image page: {response.status_code}\n'
                        f'Response body: {response.content}')

    image_soup = BeautifulSoup(response.text, 'html.parser')

    # Подбираем разрешение не больше 2500×2500
    image_url = None
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
    if not image_url:
        return None

    # Собираем лицензии
    image_licenses = []
    license_tags = image_soup.find_all(class_=re.compile('licensetpl_short'))
    for tag in license_tags:
        clean_text = re.sub(r'\s+', ' ', tag.get_text(strip=True)).strip()
        image_licenses.append(clean_text)
    if not image_licenses:
        return None

    image_licenses = sorted(set(image_licenses))

    if netloc == 'web.archive.org':
        lst = image_url.split('https://')
        lst[1] = lst[1][:-1] + 'if_/'
        req = get_request('https://'.join(lst))
        if req.status_code != 200:
            return None
        image_url = req.url

    # Получаем автора (в виде HTML, совместимого с Telegram Bot API)
    image_author_html = extract_from_next(image_soup, 'fileinfotpl_aut')

    # Получаем источник, если автор неизвестен
    if not image_author_html or any(word in image_author_html.lower() for word in ('неизвест', 'аноним', 'unknown')):
        source_html = extract_from_next(image_soup, 'fileinfotpl_src')
        if source_html:
            image_author_html = 'неизвестен, источник: ' + source_html
    if not image_author_html:
        return None

    return Image(
        url=image_url,
        licenses=image_licenses,
        page_url=image_page_url,
        author_html=image_author_html,
    )


def get_featured_article(last_title: str, wiki_url: str) -> Optional[Article]:
    response = get_request(wiki_url)
    if response.status_code != 200:
        raise Exception(f'Unexpected response code when get wiki page: {response.status_code}\n'
                        f'Response body: {response.content}')
    response.encoding = 'utf-8'
    soup = clean_soup(BeautifulSoup(response.text, 'html.parser'))

    # Определяем блок с избранной статьёй
    if '/Заглавная_страница' in wiki_url or '/Main_Page' in wiki_url:
        featured_block = soup.find('div', id='main-tfa' if '/Заглавная_страница' in wiki_url else 'mp-tfa')
        link_tag = featured_block.find('a', href=True)
        title = link_tag['title']
        if title == last_title:
            return None
        _, article_link = get_url_by_tag(wiki_url, link_tag)
        paragraphs = [p.get_text().strip() for p in featured_block.find_all('p')]
    else:
        # Или воспринимаем произвольную статью как избранную
        featured_block = soup.find('div', id='mw-content-text')
        title = soup.find('h1', id='firstHeading').get_text().strip()
        if title == last_title:
            return None
        article_link = wiki_url
        paragraphs = [p.get_text().strip() for p in featured_block.find_all('p')]

    img_tag = featured_block.find('img')
    image = get_image_by_src(wiki_url, img_tag)

    return Article(
        title=title,
        paragraphs=paragraphs,
        link=article_link,
        image=image,
    )


def get_trimmed_text(paragraphs, max_length):
    total_length, text = 0, ''
    for paragraph in paragraphs:
        paragraph = remove_brackets(paragraph)
        paragraph_length = len(paragraph) + 2
        text += paragraph
        if total_length + paragraph_length > max_length:
            t = str(text[:max_length - 2].rsplit('.', 1)[0])
            # режем дальше, если обрезали на аббревиатуре/инициале
            while len(t) > 1 and t[-2].isspace() and t[-1].upper() == t[-1]:
                t = str(t.rsplit('.', 1)[0])
            return t + '.\n\n'
        text += '\n\n'
        total_length += paragraph_length
    return text


def send_to_telegram(article: Article, telegram_channels, rules_url):
    caption_beginning = f"<b>{article.title}</b>\n\n"
    caption_end = (
        f"<a href='{article.link}'>Читать статью</a>\n\n"
        f"<a href='{rules_url}'>Лицензия на текст: CC BY-SA</a>\n"
    )

    # Дополняем caption_end, вычисляем максимальную длину под остальной текст
    if article.image:
        # Специальные лицензии
        special_licenses = {
            "Public domain": "Общественное достояние",
            "PDM": "Общественное достояние",
            "CC0": "CC0"
        }

        # Проверяем, есть ли специальные лицензии
        special_license = None
        for key, text in special_licenses.items():
            if key in article.image.licenses:
                special_license = text
                break

        # Добавляем лицензии
        caption_end += f"<a href='{article.image.page_url}'>"
        if special_license or len(article.image.licenses) == 1:
            caption_end += f"Лицензия на изображение: {special_license or article.image.licenses[0]}"
        else:
            caption_end += f"Лицензии на изображение: {", ".join(article.image.licenses)}"
        caption_end += "</a>"

        # Добавляем автора
        caption_end += f" (автор: {article.image.author_html})"

        max_text_len = 1024 - visible_length(caption_beginning) - visible_length(caption_end)
    else:
        max_text_len = 4096 - visible_length(caption_beginning) - visible_length(caption_end)

    # Формируем подпись и отправляем сообщение в каждый канал
    caption = caption_beginning + get_trimmed_text(article.paragraphs, max_text_len) + caption_end
    if article.image:
        for channel in telegram_channels:
            bot.send_photo(channel, article.image.url, caption=caption, parse_mode='HTML')
    else:
        for channel in telegram_channels:
            bot.send_message(channel, caption, parse_mode='HTML')


def main(config: Config):
    last_title = read_last_article(config.LAST_ARTICLE_FILE)
    article = get_featured_article(last_title, config.WIKI_URL)

    if article:
        send_to_telegram(article, config.TELEGRAM_CHANNELS, config.RULES_URL)
        write_last_article(article.title, config.LAST_ARTICLE_FILE)
        print(f'Избрана новая статья: {article.title}')
    else:
        print('Избранная статья не изменилась')
