import io
import os
import re
import sys
import requests
import telebot
from bs4 import BeautifulSoup
from config import Config

# stdout/stderr → UTF-8 для корректной кириллицы
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_featured_article(WIKI_URL):
    response = requests.get(WIKI_URL)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    featured_block = soup.find('div', id='main-tfa' if '/Заглавная_страница' in WIKI_URL else 'mw-content-text')
    paragraphs = [p.get_text().strip() for p in featured_block.find_all('p')]
    link_tag = featured_block.find('a', href=True)
    title = link_tag['title'] if '/Заглавная_страница' in WIKI_URL else WIKI_URL
    article_link = f"https://ru.wikipedia.org{link_tag['href']}"
    img_tag = featured_block.find('img')

    image_url, image_licenses, image_page_url = None, [], None

    if img_tag and img_tag.has_attr('src') and img_tag.parent.has_attr('href'):
        image_page_url = 'https://ru.wikipedia.org' + img_tag.parent['href']
        image_response = requests.get(image_page_url)
        image_soup = BeautifulSoup(image_response.text, 'html.parser')

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

        license_tags = image_soup.find_all(class_=re.compile('licensetpl_short'))
        for tag in license_tags:
            clean_text = re.sub(r'\s+', ' ', tag.get_text(strip=True)).strip()
            image_licenses.append(clean_text)

    image_licenses = list(set(image_licenses))
    return title, paragraphs, image_url, article_link, image_licenses, image_page_url


def trim_paragraphs(paragraphs, max_length=900):
    total_length, text = 0, ''
    for paragraph in paragraphs:
        paragraph_length = len(paragraph) + 2
        text += paragraph
        if total_length + paragraph_length > max_length:
            t = str(text[:max_length].rsplit('.', 1)[0])
            while len(t) > 1 and t[-2].isspace() and t[-1].upper() == t[-1]:
                t = str(t.rsplit('.', 1)[0])
            return t + '.'
        text += '\n\n'
        total_length += paragraph_length
    return text[:-2]


def read_last_article(LAST_ARTICLE_FILE):
    if not os.path.exists(LAST_ARTICLE_FILE):
        return ''
    with open(LAST_ARTICLE_FILE, 'r', encoding='utf-8') as file:
        return file.read().strip()


def write_last_article(title, LAST_ARTICLE_FILE):
    with open(LAST_ARTICLE_FILE, 'w', encoding='utf-8') as file:
        file.write(title)


def send_to_telegram(title, paragraphs, image_url, link, image_licenses, image_page_url,
                     TELEGRAM_CHANNELS, RULES_URL):
    trimmed_text = trim_paragraphs(paragraphs)
    caption = (
        f"<b>{title}</b>\n\n{trimmed_text}\n\n"
        f"<a href='{link}'>Читать статью</a>\n\n"
        f"<a href='{RULES_URL}'>Лицензия на текст: CC BY-SA</a>\n"
    )

    if image_licenses:
        if "Public domain" in image_licenses or "PDM" in image_licenses:
            caption += f"<a href='{image_page_url}'>Лицензия на изображение: Общественное достояние</a>"
        elif len(image_licenses) == 1:
            caption += f"<a href='{image_page_url}'>Лицензия на изображение: {image_licenses[0]}</a>"
        else:
            caption += f"<a href='{image_page_url}'>Лицензии на изображение: " + ", ".join(image_licenses) + "</a>"

    for channel in TELEGRAM_CHANNELS:
        if image_url:
            bot.send_photo(channel, image_url, caption=caption, parse_mode='HTML')
        else:
            bot.send_message(channel, caption, parse_mode='HTML')


def main(config: Config):
    title, paragraphs, image_url, link, image_licenses, image_page_url = get_featured_article(config.WIKI_URL)
    last_title = read_last_article(config.LAST_ARTICLE_FILE)

    if title != last_title:
        send_to_telegram(title, paragraphs, image_url, link, image_licenses, image_page_url,
                         config.TELEGRAM_CHANNELS, config.RULES_URL)
        write_last_article(title, config.LAST_ARTICLE_FILE)
        print(f'Избрана новая статья: {title}')
    else:
        print('Избранная статья не изменилась')
