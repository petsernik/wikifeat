import io
import re
import sys
from typing import Optional
from urllib.parse import urlparse

import telebot
from bs4 import BeautifulSoup
from bs4.element import Tag

from config import Config, TELEGRAM_BOT_TOKEN, TEXT_IMAGE_PATH
from i18n import TKey
from models import Article, Image, ArticleContext
from parsers import LANG_PARSERS
from utils import (
    get_request,
    get_url_by_context,
    get_url_by_tag,
    clean_soup,
    remove_brackets,
    read_last_article,
    write_last_article,
    visible_length,
    extract_attrs_info,
    html_to_text,
    replace_links_with_numbers,
    update_links,
    draw_centered_text,
    is_balanced,
    ends_with_one_char_abbr,
    normalize_url,
)

# stdout/stderr → UTF-8 для корректной кириллицы
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_image_by_tag(netloc: str, main_block: Tag, ctx: ArticleContext) -> Optional[Image]:
    img_tag = main_block.select_one('a[href] img')
    if not img_tag:
        return None
    image_page_url = get_url_by_tag(netloc, img_tag)
    return get_image_by_link(image_page_url, ctx)


def get_image_by_link(image_page_url: str, ctx: ArticleContext) -> Optional[Image]:
    netloc = urlparse(image_page_url).netloc
    response = get_request(image_page_url)
    if response.status_code in (404, 429):
        return None
    if response.status_code != 200:
        raise Exception(f'Unexpected response code when get image page: {response.status_code}\n'
                        f'Response body: {response.content}')

    image_soup = BeautifulSoup(response.text, 'html.parser')

    # Подбираем разрешение не больше 2000×2000
    image_url = None
    width_max, height_max = 2000, 2000
    resolutions_span = image_soup.find('span', class_='mw-filepage-other-resolutions')
    if resolutions_span:
        links = resolutions_span.find_all('a', href=True)
        for link in links[::-1]:
            clean_text = re.sub(r'[\s,.]+', '', link.text)
            match = re.search(r'(\d+)[×xX](\d+)', clean_text)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                if width <= width_max and height <= height_max:
                    image_url = get_url_by_tag(netloc, link)
                    break
    else:
        file_link_tag = image_soup.find('a', class_='internal')
        if file_link_tag and file_link_tag.has_attr('href'):
            image_url = get_url_by_tag(netloc, file_link_tag)
    if not image_url:
        return None

    raw_licenses = {re.sub(r'\s+', ' ', tag.get_text(strip=True)) for tag in
                    image_soup.find_all(class_=re.compile('licensetpl_short'))}
    if not raw_licenses:
        return None

    fair_use_keywords = {ctx.t(TKey.FAIR_USE), "Fair use"}
    if not raw_licenses.isdisjoint(fair_use_keywords):
        return None

    replacements = {
        "CC BY-SA 4.0": "CC BY-SA",
        "CC BY 4.0": "CC BY"
    }
    image_licenses = {replacements.get(lic, lic) for lic in raw_licenses}

    cc0 = "CC0"
    pdm = ctx.t(TKey.PUBLIC_DOMAIN)
    pd_licenses_map = {
        "Public domain": pdm,
        "PDM": pdm,
        "CC0": cc0
    }

    pd_keys = set(pd_licenses_map.keys())
    if not image_licenses.issubset(pd_keys):
        image_licenses -= pd_keys
    elif "CC0" in image_licenses:
        image_licenses = {cc0}
    else:
        image_licenses = {pdm}

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
            image_author_html = ctx.t(TKey.AUTHOR_MULTIPLE, author=image_author_html)
        else:
            image_author_html = ctx.t(TKey.AUTHOR_SINGLE, author=image_author_html)

    # Получаем источник, если автор неизвестен
    if not image_author_html or any(
            word in image_author_text.lower()
            for word in ('не указан', 'неизвест', 'аноним', 'unknown', 'unbekannt')
    ):
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
            source_html = ctx.t(TKey.SOURCE_MULTIPLE, source=source_html)
        else:
            source_html = ctx.t(TKey.SOURCE_SINGLE, source=source_html)

        image_author_html = f"{ctx.t(TKey.AUTHOR_UNKNOWN)}, {source_html}"

    if not image_author_html:
        return None

    image_author_html = update_links(netloc, image_author_html)
    return Image(
        desc=image_url,
        licenses=sorted(image_licenses),
        page_url=image_page_url,
        author_html=image_author_html,
    )


def get_image_by_text(text: str, ctx: ArticleContext) -> Optional[Image]:
    img = draw_centered_text(text)
    if not img:
        return None
    img.save(TEXT_IMAGE_PATH)
    return Image(
        desc=TEXT_IMAGE_PATH,
        licenses=['CC0'],
        page_url='https://typodermicfonts.com/public-domain/',
        author_html=ctx.t(TKey.FONTS_AUTHOR, author='Ray Larabie')
    )


def get_featured_article(last_title: str, ctx: ArticleContext) -> Optional[Article]:
    response = get_request(get_url_by_context(ctx))
    if response.status_code != 200:
        raise Exception(f'Unexpected response code when get wiki page: {response.status_code}\n'
                        f'Response body: {response.content}')
    response.encoding = 'utf-8'
    parser = LANG_PARSERS.get(ctx.lang) or LANG_PARSERS['en']
    soup = clean_soup(BeautifulSoup(response.text, 'html.parser'))
    url = normalize_url(response.url)
    article, netloc, main_block = parser(soup, url, last_title)
    if not article:
        return None
    if ctx.with_image:
        article.image = get_image_by_tag(netloc, main_block, ctx) or get_image_by_text(article.title, ctx)
    return article


def get_trimmed_text(paragraphs: list[str], max_length: int) -> str:
    total_length, text = 0, ''
    for paragraph in paragraphs:
        paragraph = remove_brackets(paragraph)
        paragraph_length = len(paragraph) + 2
        text += paragraph
        if total_length + paragraph_length > max_length:
            ok, i = False, max_length - 2
            t = text[:i]

            while not ok:
                t = str(t[:i].rsplit('.', 1)[0])
                while ends_with_one_char_abbr(t):
                    split = t.rsplit('.', 1)
                    if len(split) == 1:
                        return t + '.\n\n'  # Я верю, что это невозможный случай в данном контексте
                    t = split[0]
                ok, i = is_balanced(t)

            return t + '.\n\n'
        text += '\n\n'
        total_length += paragraph_length
    return text


def get_caption(article: Article, rules_url: str, ctx: ArticleContext) -> str:
    caption_beginning = f"<b><a href='{article.link}'>{article.title}</a></b>\n\n"

    caption_end = (
        f"<a href='{article.link}'>{ctx.t(TKey.READ_ARTICLE)}</a>\n\n"
        f"<a href='{rules_url}'>{ctx.t(TKey.TEXT_LICENSE)}</a>\n"
    )

    # Дополняем caption_end, вычисляем максимальную длину под остальной текст
    if article.image:
        # Добавляем лицензии
        caption_end += f"<a href='{article.image.page_url}'>"

        if len(article.image.licenses) == 1:
            caption_end += ctx.t(
                TKey.IMAGE_LICENSE_SINGLE,
                license=article.image.licenses[0]
            )
        else:
            caption_end += ctx.t(
                TKey.IMAGE_LICENSE_MULTIPLE,
                licenses=", ".join(article.image.licenses)
            )

        caption_end += "</a>"

        # Добавляем автора
        caption_end += f" ({article.image.author_html})"

        max_text_len = 1024 - visible_length(caption_beginning) - visible_length(caption_end)
    else:
        max_text_len = 4096 - visible_length(caption_beginning) - visible_length(caption_end)

    return caption_beginning + get_trimmed_text(article.paragraphs, max_text_len) + caption_end


def send_to_telegram(article: Article, telegram_channels: list[str], rules_url: str, ctx: ArticleContext):
    # Формируем подпись и отправляем сообщение в каждый канал
    print(f'[LOG] Trying to send {article.title} ({article.link}) to telegram channels')
    caption = get_caption(article, rules_url, ctx)
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


def run(config: Config) -> bool:
    if not config.WIKI_URL_OR_NAME:
        raise Exception(f'This option is not supported for this language ({config.LANG_CODE}), please use '
                        f'TRANSLATIONS[lang][TKey.MAIN_PAGE] instead (or update i18n.py file)')
    last_title = read_last_article(config.LAST_ARTICLE_FILE)
    ctx = ArticleContext(lang=config.LANG_CODE, url_or_name=config.WIKI_URL_OR_NAME, with_image=config.WITH_IMAGE)
    article = get_featured_article(last_title, ctx)

    if not article:
        print(ctx.t(TKey.ARTICLE_NOT_CHANGED))
        return False

    send_to_telegram(article, config.TELEGRAM_CHANNELS, config.RULES_URL, ctx)
    write_last_article(article.title, config.LAST_ARTICLE_FILE)
    print(ctx.t(TKey.NEW_ARTICLE_SELECTED, title=article.title))
    return True
