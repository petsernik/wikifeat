import io
import os
import re
import sys

import requests
import telebot
from bs4 import BeautifulSoup

# Устанавливаем stdout/stderr на UTF-8 для корректного отображения кириллицы в MINGW64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройки
TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
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

    featured_block = soup.find('div', id='main-tfa' if '/Заглавная_страница' in WIKI_URL else 'mw-content-text')
    paragraphs = [p.get_text().strip() for p in featured_block.find_all('p')]
    link_tag = featured_block.find('a', href=True)
    title = link_tag['title']
    article_link = f"https://ru.wikipedia.org{link_tag['href']}"
    img_tag = featured_block.find('img')

    image_url = None
    image_licenses = []  # Список всех лицензий
    image_page_url = None

    if img_tag and img_tag.has_attr('src') and img_tag.parent.has_attr('href'):
        image_page_url = 'https://ru.wikipedia.org' + img_tag.parent['href']
        image_response = requests.get(image_page_url)
        image_soup = BeautifulSoup(image_response.text, 'html.parser')

        # Ищем изображения в других разрешениях
        # Причина: через telebot нельзя прикрепить изображение > 10 Mb
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
            # Старый способ: URL полного изображения
            file_link_tag = image_soup.find('a', class_='internal')
            if file_link_tag and file_link_tag.has_attr('href'):
                image_url = 'https:' + file_link_tag['href']

        # Собираем ВСЕ лицензии изображения со страницы
        license_tags = image_soup.find_all(class_=re.compile('licensetpl_short'))
        for tag in license_tags:
            license_text = tag.get_text(strip=True)

            # Очистка текста
            clean_text = re.sub(r'\s+', ' ', license_text).strip()

            # Сохраняем как текст
            image_licenses.append(clean_text)

    # унифицируем названия лицензий на случай повторов
    image_licenses = list(set(image_licenses))

    return title, paragraphs, image_url, article_link, image_licenses, image_page_url


def trim_paragraphs(paragraphs, max_length=900):
    """Выделяет абзацы с суммарной длиной <= max_length."""
    # Причина: подпись к изображению не может превышать 1024 символов (при использовании ботов)
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
        return text[:max_length].rsplit('.', 1)[0] + '.'

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


def send_to_telegram(title, paragraphs, image_url, link, image_licenses, image_page_url):
    """Отправка сообщения в канал"""
    trimmed_text = trim_paragraphs(paragraphs)
    caption = (
        f"<b>{title}</b>\n\n{trimmed_text}\n\n"
        f"<a href='{link}'>Читать статью</a>\n\n"
        f"<a href='{RULES_URL}'>Лицензия на текст: CC BY-SA</a>\n"
    )

    # Добавляем все лицензии изображения
    if image_licenses:
        if "Public domain" in image_licenses or "PDM" in image_licenses:
            caption += f"<a href='{image_page_url}'>Лицензия на изображение: Общественное достояние</a>"
        elif len(image_licenses) == 1:
            caption += f"<a href='{image_page_url}'>Лицензия на изображение: {image_licenses[0]}</a>"
        else:
            caption += f"<a href='{image_page_url}'>Лицензии на изображение: " + ", ".join(image_licenses) + "</a>"

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
    title, paragraphs, image_url, link, image_licenses, image_page_url = get_featured_article()
    last_title = read_last_article()

    if title != last_title:
        send_to_telegram(title, paragraphs, image_url, link, image_licenses, image_page_url)
        write_last_article(title)
        print(f'Избрана новая статья: {title}')
    else:
        print('Избранная статья не изменилась')


if __name__ == '__main__':
    main()
