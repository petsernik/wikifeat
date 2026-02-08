import io
import re
import sys
from typing import Optional
from urllib.parse import urlparse

import telebot
from bs4 import BeautifulSoup

from config import Config, TELEGRAM_BOT_TOKEN
from models import Article, Image
from utils import (
    get_request,
    get_url_by_tag,
    clean_soup,
    remove_brackets,
    read_last_article,
    write_last_article,
    visible_length,
    extract_attrs_info,
    html_to_text,
    replace_links_with_numbers,
    draw_centered_text,
)

# stdout/stderr → UTF-8 для корректной кириллицы
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
            match = re.search(r'([\d,]+)\s*[×xX]\s*([\d,]+)', link.text)
            if match:
                width = int(match.group(1).replace(',', '').replace(' ', ''))
                height = int(match.group(2).replace(',', '').replace(' ', ''))
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

    # Игнорируем несвободные материалы
    if any(fair_use in image_licenses for fair_use in ["Добросовестное использование", "Fair use"]):
        return None

    # Я верю, что 4.0 - последняя версия, так что 4.0 не буду писать,
    # а если и появятся когда-нибудь версии поновее, то я ведь и
    # ссылку указываю, перейдя по которой можно узнать что подразумевалась 4.0
    for i in range(len(image_licenses)):
        if image_licenses[i] == "CC BY-SA 4.0":
            image_licenses[i] = "CC BY-SA"
        elif image_licenses[i] == "CC BY 4.0":
            image_licenses[i] = "CC BY"

    if netloc == 'web.archive.org':
        lst = image_url.split('https://')
        lst[1] = lst[1][:-1] + 'if_/'
        req = get_request('https://'.join(lst))
        if req.status_code != 200:
            return None
        image_url = req.url

    # Сначала пробуем найти licensetpl_attr (требуемую атрибуцию)
    image_author_html = extract_attrs_info(
        image_soup,
        find_kwargs={'class': 'licensetpl_attr'},
        next_tags=None
    )

    # Очень специальный случай... (считаю что лучше бы так сразу и было указано в разделе licensetpl_attr)
    if image_author_html and "Diego Delso" in image_author_html:
        image_author_html = image_author_html.replace(
            "Diego Delso",
            "Diego Delso, <a href=\"https://delso.photo\">delso.photo</a>",
        )

    # Если не нашли, то получаем автора из соответствующего поля
    if not image_author_html:
        image_author_html = extract_attrs_info(
            image_soup,
            find_kwargs={'id': 'fileinfotpl_aut'},
            next_tags=('td', 'th')
        )

    image_author_text = ''
    if image_author_html:
        image_author_text = html_to_text(image_author_html)
        if ',' in image_author_text or ';' in image_author_text:
            image_author_html = 'автор(ы): ' + image_author_html
        else:
            image_author_html = 'автор: ' + image_author_html

    # Получаем источник, если автор неизвестен
    if not image_author_html or any(word in image_author_text.lower() for word in ('не указан', 'неизвест',
                                                                                   'аноним', 'unknown')):
        source_html = extract_attrs_info(
            image_soup,
            find_kwargs={'id': 'fileinfotpl_src'},
            next_tags=('td', 'th')
        )
        if not source_html:
            return None

        source_html = replace_links_with_numbers(source_html)
        source_text = html_to_text(source_html)
        if ',' in source_text or ';' in source_text:
            source_html = 'источники: ' + source_html
        else:
            source_html = 'источник: ' + source_html
        image_author_html = 'автор неизвестен, ' + source_html
    if not image_author_html:
        return None

    return Image(
        desc=image_url,
        licenses=image_licenses,
        page_url=image_page_url,
        author_html=image_author_html,
    )


def get_featured_article(last_title: str, wiki_url: str, with_image=True) -> Optional[Article]:
    response = get_request(wiki_url)
    if response.status_code != 200:
        raise Exception(f'Unexpected response code when get wiki page: {response.status_code}\n'
                        f'Response body: {response.content}')
    response.encoding = 'utf-8'
    soup = clean_soup(BeautifulSoup(response.text, 'html.parser'))

    # Определяем блок с избранной статьёй
    path = urlparse(wiki_url).path
    if path.endswith('/wiki/Заглавная_страница'):
        main_block = soup.find('div', id='main-tfa')
        link_tag = main_block.find('a', href=True)
        title = link_tag['title']
        block_type = main_block.find('div', class_='main-box-subtitle').get_text().strip()
        if not title or title == last_title or block_type != 'Избранная статья':
            return None
        _, article_link = get_url_by_tag(wiki_url, link_tag)
        paragraphs = [p.get_text().strip() for p in main_block.find_all('p')]
    elif path.endswith('/wiki/Main_Page'):
        main_block = soup.find('div', id='mp-tfa')
        # На английской главной ищем ссылку на полную статью по фразе "Full article..." или "more..."
        link_tag = main_block.find(
            'a', string=lambda s: s and s.strip().replace('\xa0', ' ') in ('Full article...', 'more...')
        )
        if not link_tag:
            raise Exception("Unexpected parse case")
        title = link_tag.get('title')
        if title == last_title:
            return None
        _, article_link = get_url_by_tag(wiki_url, link_tag)
        paragraphs = [p.get_text().strip() for p in main_block.find_all('p')]
    else:
        # Любая другая статья — воспринимаем как избранную (корректно обработает, даже если не избранная)
        main_block = soup.find('div', id='mw-content-text')
        title = soup.find('h1', id='firstHeading').get_text().strip()
        if title == last_title:
            return None
        article_link = wiki_url
        paragraphs = [p.get_text().strip() for p in main_block.find_all('p')]

    article = Article(
        title=title,
        paragraphs=paragraphs,
        link=article_link,
        image=None,
    )
    if not with_image:
        return article

    img_tag = main_block.find('img')
    image = get_image_by_src(wiki_url, img_tag)
    if image:
        article.image = image
        return article

    img = draw_centered_text(title)
    if not img:
        return article

    img.save('image.jpg')
    article.image = Image(
        desc='image.jpg',
        licenses=['CC0'],
        page_url='https://typodermicfonts.com/public-domain/',
        author_html='автор шрифта: Ray Larabie'
    )
    return article


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
        caption_end += f" ({article.image.author_html})"

        max_text_len = 1024 - visible_length(caption_beginning) - visible_length(caption_end)
    else:
        max_text_len = 4096 - visible_length(caption_beginning) - visible_length(caption_end)

    # Формируем подпись и отправляем сообщение в каждый канал
    caption = caption_beginning + get_trimmed_text(article.paragraphs, max_text_len) + caption_end
    if not article.image:
        for channel in telegram_channels:
            bot.send_message(channel, caption, parse_mode='HTML')
        return
    if article.image.desc.startswith('https://'):
        for channel in telegram_channels:
            bot.send_photo(channel, article.image.desc, caption=caption, parse_mode='HTML')
        return
    with open(article.image.desc, 'rb') as img:
        for channel in telegram_channels:
            bot.send_photo(channel, img, caption=caption, parse_mode='HTML')


def main(config: Config, with_image=True):
    last_title = read_last_article(config.LAST_ARTICLE_FILE)
    article = get_featured_article(last_title, config.WIKI_URL, with_image=with_image)

    if article:
        send_to_telegram(article, config.TELEGRAM_CHANNELS, config.RULES_URL)
        write_last_article(article.title, config.LAST_ARTICLE_FILE)
        print(f'Избрана новая статья: {article.title}')
    else:
        print('Избранная статья не изменилась')
