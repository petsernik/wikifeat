import io
import os
import re
import sys

import requests
import telebot
from bs4 import BeautifulSoup

# Устанавливаем stdout/stderr на UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройки
TELEGRAM_BOT_TOKEN = sys.argv[1]
TELEGRAM_CHANNELS = ['@wikifeattest']
WIKI_URL = 'https://ru.wikipedia.org/wiki/Заглавная_страница'
RULES_URL = 'https://t.me/wikifeat/4'
LAST_ARTICLE_FILE = 'last_article_test.txt'

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_featured_article():
    """Получает статью и собирает все лицензии изображения"""
    response = requests.get(WIKI_URL)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    featured_block = soup.find('div', id='main-tfa')
    title = featured_block.find('b').text.strip()
    paragraphs = [p.get_text().strip() for p in featured_block.find_all('p')]
    link_tag = featured_block.find('a', href=True)
    article_link = f"https://ru.wikipedia.org{link_tag['href']}"
    img_tag = featured_block.find('img')

    full_image_url = None
    image_licenses = []  # Список всех лицензий
    image_page_url = None

    if img_tag and img_tag.has_attr('src') and img_tag.parent.has_attr('href'):
        thumbnail_url = 'https:' + img_tag['src']
        image_page_url = 'https://ru.wikipedia.org' + img_tag.parent['href']
        image_response = requests.get(image_page_url)
        image_soup = BeautifulSoup(image_response.text, 'html.parser')

        # URL полного изображения
        file_link_tag = image_soup.find('a', class_='internal')
        if file_link_tag and file_link_tag.has_attr('href'):
            full_image_url = 'https:' + file_link_tag['href']

        # Собираем ВСЕ лицензии со страницы
        license_tags = image_soup.find_all(class_=re.compile('licensetpl_short'))
        for tag in license_tags:
            license_text = tag.get_text(strip=True)
            license_link = tag.find('a', href=True)
            license_url = license_link['href'] if license_link else None

            # Очистка текста
            clean_text = re.sub(r'\s+', ' ', license_text).strip()

            # Нормализация URL
            if license_url:
                if license_url.startswith('//'):
                    license_url = 'https:' + license_url
                elif license_url.startswith('/'):
                    license_url = 'https://commons.wikimedia.org' + license_url

            # Сохраняем как (текст, url)
            image_licenses.append((clean_text, license_url))

    return title, paragraphs, full_image_url, article_link, image_licenses, image_page_url


def trim_paragraphs(paragraphs, max_length=800):
    """Оптимизация текста для Telegram"""
    trimmed_paragraphs = []
    total_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph) + 2  # +2 для переносов
        if total_length + paragraph_length > max_length:
            break
        trimmed_paragraphs.append(paragraph)
        total_length += paragraph_length

    if len(trimmed_paragraphs) == 0 and len(paragraphs) > 0:
        text = paragraphs[0]
        return text[:max_length].rsplit('.', 1)[0] + '.'

    return '\n\n'.join(trimmed_paragraphs)


def read_last_article():
    if not os.path.exists(LAST_ARTICLE_FILE):
        return ''
    with open(LAST_ARTICLE_FILE, 'r', encoding='utf-8') as f:
        return f.read().strip()


def write_last_article(title):
    with open(LAST_ARTICLE_FILE, 'w', encoding='utf-8') as f:
        f.write(title)


def send_to_telegram(title, paragraphs, image_url, link, image_licenses, image_page_url):
    """Отправляет сообщение со всеми лицензиями изображения"""
    trimmed_text = trim_paragraphs(paragraphs)
    caption = (
        f"<b>{title}</b>\n\n{trimmed_text}\n\n"
        f"<a href='{link}'>Читать статью</a>\n\n"
        f"<a href='{RULES_URL}'>Лицензия на текст: CC BY-SA</a>"
    )

    # Добавляем все лицензии изображения
    if image_licenses:
        caption += "\n\n<b>Лицензии изображения:</b>"
        for i, (text, url) in enumerate(image_licenses, 1):
            if url:
                caption += f"\n{i}. <a href='{url}'>{text}</a>"
            else:
                caption += f"\n{i}. {text}"

    # Всегда добавляем ссылку на страницу изображения
    if image_page_url:
        caption += f"\n\n<a href='{image_page_url}'>Страница изображения со всеми лицензиями</a>"

    for channel in TELEGRAM_CHANNELS:
        if image_url:
            try:
                bot.send_photo(
                    channel,
                    image_url,
                    caption=caption,
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Ошибка отправки фото: {e}")
                bot.send_message(channel, caption, parse_mode='HTML')
        else:
            bot.send_message(channel, caption, parse_mode='HTML')


def main():
    try:
        title, paragraphs, image_url, link, image_licenses, image_page_url = get_featured_article()
        last_title = read_last_article()

        if title != last_title:
            print(f'Новая статья: {title}')
            send_to_telegram(title, paragraphs, image_url, link, image_licenses, image_page_url)
            write_last_article(title)
        else:
            print('Статья не изменилась')
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == '__main__':
    main()