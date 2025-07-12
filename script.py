import io
import os
import sys

import requests
import telebot
from bs4 import BeautifulSoup

# Устанавливаем stdout/stderr на UTF-8 для корректного отображения русских символов в MINGW64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройки
TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
TELEGRAM_CHANNELS = ['@wikifeat']  # Список каналов Telegram
WIKI_URL = 'https://ru.wikipedia.org/wiki/Заглавная_страница'
RULES_URL = 'https://t.me/wikifeat/4'
LAST_ARTICLE_FILE = 'last_article.txt'

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_featured_article():
    """Получает заголовок и полный текст текущей избранной статьи."""
    response = requests.get(WIKI_URL)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    featured_block = soup.find('div', id='main-tfa')
    title = featured_block.find('b').text.strip()
    paragraphs = [p.get_text().strip() for p in featured_block.find_all('p')]
    link_tag = featured_block.find('a', href=True)
    article_link = f"https://ru.wikipedia.org{link_tag['href']}"
    img_tag = featured_block.find('img')
    if img_tag and img_tag.has_attr('src') and img_tag.parent.has_attr('href'):
        thumbnail_url = 'https:' + img_tag['src']
        image_page_link = 'https://ru.wikipedia.org' + img_tag.parent['href']
        image_response = requests.get(image_page_link)
        image_soup = BeautifulSoup(image_response.text, 'html.parser')
        file_link_tag = image_soup.find('a', class_='internal')
        full_image_url = (
            'https:' + file_link_tag['href']
            if file_link_tag.has_attr('href') else thumbnail_url
        )
    else:
        full_image_url = None

    return title, paragraphs, full_image_url, article_link


def trim_paragraphs(paragraphs, max_length=900):
    """Выделяет абзацы с суммарной длиной <= max_length."""
    trimmed_paragraphs = []
    total_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph) + 2  # +2 для двух переносов строк
        if total_length + paragraph_length > max_length:
            break
        trimmed_paragraphs.append(paragraph)
        total_length += paragraph_length

    if len(trimmed_paragraphs) == 0 and len(paragraphs) > 0:
        text = paragraphs[0]
        return text[:max_length].rsplit('.', 1)[0]+'.'

    return '\n\n'.join(trimmed_paragraphs)


def read_last_article():
    """Читает заголовок последней опубликованной статьи из файла."""
    if not os.path.exists(LAST_ARTICLE_FILE):
        return ''
    with open(LAST_ARTICLE_FILE, 'r', encoding='utf-8') as file:
        return file.read().strip()


def write_last_article(title):
    """Записывает заголовок текущей избранной статьи в файл."""
    with open(LAST_ARTICLE_FILE, 'w', encoding='utf-8') as file:
        file.write(title)


def send_to_telegram(title, paragraphs, image_url, link):
    """Отправляет краткое сообщение с избранной статьёй в Telegram-каналы."""
    trimmed_text = trim_paragraphs(paragraphs)
    caption = (
        f"<b>{title}</b>\n\n{trimmed_text}\n\n"
        f"<a href='{link}'>Читать статью</a>\n\n"
        f"<a href='{RULES_URL}'>Лицензия на текст: CC BY-SA</a>"
    )

    for channel in TELEGRAM_CHANNELS:
        if image_url:
            bot.send_photo(
                channel,
                image_url,
                caption=caption,
                parse_mode='HTML'
            )
        else:
            bot.send_message(
                channel,
                caption,
                parse_mode='HTML'
            )


def main():
    """Выполняет проверку один раз и завершает работу."""
    title, paragraphs, image_url, link = get_featured_article()
    last_title = read_last_article()

    if title != last_title:
        print(f'Избрана новая статья: {title}.')
        send_to_telegram(title, paragraphs, image_url, link)
        write_last_article(title)
    else:
        print('Избранная статья не изменилась.')


if __name__ == '__main__':
    main()
