import asyncio
import io
import re
import sys
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag
from telegram.ext import ContextTypes

from constants import SELF_MADE_IMAGE_CASE, DB_TEST_NAME, DB_NAME
from db import close_db, init_db, get_last_article, set_last_article, get_cached_final_url, article_cached, \
    get_article_from_db, set_cached_final_url, save_article_to_db, update_image_desc, update_featured_articles_in_db
from filter import is_article
from i18n import TKey, is_unknown_author
from models import Article, Image, ArticleContext, ArticleContextRequest, Config, get_app
from parsers import LANG_PARSERS
from utils import (
    get_request,
    get_quote_url_by_context,
    get_quote_url_by_tag,
    clean_soup,
    remove_brackets_by_rules,
    visible_length,
    extract_attrs_info,
    html_to_text,
    replace_links_with_numbers,
    update_links,
    is_balanced,
    ends_with_one_char_abbr,
    unquote_url,
    has_link,
    quote_url,
    get_img_buf_by_text,
)

# stdout/stderr → UTF-8 для корректной кириллицы
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# =========================
# IMAGE BY TAG
# =========================
def get_image_by_tag(netloc: str, main_block: Tag, ctx: ArticleContext) -> Optional[Image]:
    img_tag = main_block.select_one('a[href] img')
    if not img_tag:
        return None

    image_page_url = get_quote_url_by_tag(netloc, img_tag)
    return get_image_by_link(image_page_url, ctx)


# =========================
# IMAGE BY LINK
# =========================
def get_image_by_link(image_page_url: str, ctx: ArticleContext) -> Optional[Image]:
    if (image_page_url.endswith(":Commons-logo.svg")
            and ctx.url_or_title != ctx.t(TKey.WIKIMEDIA_COMMONS_TITLE)):
        return None

    netloc = urlparse(image_page_url).netloc
    response = get_request(image_page_url)

    if response.status_code in (404, 429):
        return None
    if response.status_code != 200:
        raise Exception(
            f'Unexpected response code when get image page: {response.status_code}\n'
            f'Response body: {response.content}'
        )

    image_soup = BeautifulSoup(response.text, 'html.parser')

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
                    image_url = get_quote_url_by_tag(netloc, link)
                    break
    else:
        file_link_tag = image_soup.find('a', class_='internal')
        if file_link_tag and file_link_tag.has_attr('href'):
            image_url = get_quote_url_by_tag(netloc, file_link_tag)

    if not image_url:
        return None

    raw_licenses = {
        re.sub(r'\s+', ' ', tag.get_text(strip=True))
        for tag in image_soup.find_all(class_=re.compile('licensetpl_short'))
    }

    if not raw_licenses:
        return None

    fair_use_keywords = {ctx.t(TKey.FAIR_USE), "Fair use"}
    if ctx.lang == 'fr':
        fair_use_keywords.add("marque déposée")
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

    # archive fix
    if netloc == 'web.archive.org':
        lst = image_url.split('https://')
        lst[1] = lst[1][:-1] + 'if_/'
        req = get_request('https://'.join(lst))
        if req.status_code != 200:
            return None
        image_url = req.url

    image_author_html = extract_attrs_info(
        image_soup,
        find_kwargs={'class': 'licensetpl_attr'},
        next_tags=None
    )

    if image_author_html and "Diego Delso" in image_author_html:
        image_author_html = image_author_html.replace(
            "Diego Delso",
            "Diego Delso, <a href=\"https://delso.photo\">delso.photo</a>",
        )

    if not image_author_html:
        image_author_html = extract_attrs_info(
            image_soup,
            find_kwargs={'id': 'fileinfotpl_aut'},
            next_tags=('td', 'th')
        )

    source_html = extract_attrs_info(
        image_soup,
        find_kwargs={'id': 'fileinfotpl_src'},
        next_tags=('td', 'th')
    )

    if not source_html:
        return None

    unknown = False

    if image_author_html:
        image_author_text = html_to_text(image_author_html)
        unknown = is_unknown_author(image_author_text)

        if not unknown:
            if not has_link(image_author_html):
                source_soup = BeautifulSoup(source_html, 'html.parser')
                links = source_soup.find_all('a', href=True)

                if len(links) == 1:
                    href = links[0].get('href')
                    image_author_html = f'<a href="{href}">{image_author_html}</a>'

            if ',' in image_author_text or ';' in image_author_text:
                image_author_html = ctx.t(TKey.AUTHOR_MULTIPLE, author=image_author_html)
            else:
                image_author_html = ctx.t(TKey.AUTHOR_SINGLE, author=image_author_html)

    if unknown or not image_author_html:
        source_html = replace_links_with_numbers(source_html)
        source_text = html_to_text(source_html)

        if ',' in source_text or ';' in source_text:
            source_html = ctx.t(TKey.SOURCE_MULTIPLE, source=source_html)
        else:
            source_html = ctx.t(TKey.SOURCE_SINGLE, source=source_html)

        image_author_html = f"{ctx.t(TKey.AUTHOR_UNKNOWN)}, {source_html}"

    image_author_html = update_links(netloc, image_author_html)

    return Image(
        desc=image_url,
        licenses=sorted(image_licenses),
        page_url=image_page_url,
        author_html=image_author_html,
        is_animation=image_url.endswith(".gif")
    )


# =========================
# IMAGE BY TEXT
# =========================
def empty_self_made_image(ctx: ArticleContext) -> Image:
    return Image(
        desc=SELF_MADE_IMAGE_CASE,
        licenses=['CC0'],
        page_url='https://typodermicfonts.com/public-domain/',
        author_html=ctx.t(TKey.FONTS_AUTHOR, author='Ray Larabie'),
        is_animation=False
    )


# =========================
# TRIM TEXT
# =========================
def get_trimmed_text(paragraphs: list[str], max_length: int) -> str:
    total_length, text = 0, ''

    for paragraph in paragraphs:
        paragraph = remove_brackets_by_rules(paragraph)
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
                        return t + '.\n\n'
                    t = split[0]

                ok, i = is_balanced(t)

            return t + '.\n\n'

        text += '\n\n'
        total_length += paragraph_length

    return text


# =========================
# CAPTION
# =========================
def get_caption(
        article: Article,
        rules_url: str,
        ctx: ArticleContext,
        *,
        use_only_first_paragraph=False,
        without_article_link=False,
        with_attribution=True,
) -> str:
    paragraphs = article.paragraphs if not use_only_first_paragraph else article.paragraphs[:1]
    caption_end = ""

    if without_article_link:
        # NOTE: CC BY-SA need you to add attribution somewhere (and many others licences too)
        max_text_len = 1024 if article.image else 4096
        if with_attribution:
            caption_end = f"<a href='{rules_url}'>{ctx.t(TKey.TEXT_ALL_PAGES_LICENSE)}</a>\n"
            max_text_len -= visible_length(caption_end)
        return get_trimmed_text(paragraphs, max_text_len) + caption_end

    caption_beginning = f"<b><a href='{article.link}'>{article.title}</a></b>\n\n"

    caption_end = (
        f"<a href='{article.link}'>{ctx.t(TKey.READ_ARTICLE)}</a>\n\n"
        f"<a href='{rules_url}'>{ctx.t(TKey.TEXT_LICENSE)}</a>\n"
    )

    if article.image:
        caption_end += f"<a href='{article.image.page_url}'>"

        if len(article.image.licenses) == 1:
            caption_end += ctx.t(TKey.IMAGE_LICENSE_SINGLE, license=article.image.licenses[0])
        else:
            caption_end += ctx.t(
                TKey.IMAGE_LICENSE_MULTIPLE,
                licenses=", ".join(article.image.licenses)
            )

        caption_end += "</a>"
        caption_end += f" ({article.image.author_html})"

        max_text_len = 1024 - visible_length(caption_beginning) - visible_length(caption_end)
    else:
        max_text_len = 4096 - visible_length(caption_beginning) - visible_length(caption_end)

    return caption_beginning + get_trimmed_text(paragraphs, max_text_len) + caption_end


# =========================
# SEND TO TARGETS (ASYNC)
# =========================
async def send_to_targets(context: ContextTypes.DEFAULT_TYPE, article: Article, targets: list[int | str],
                          rules_url: str, ctx: ArticleContext):
    caption = get_caption(article, rules_url, ctx)

    for target in targets:
        if not article.image:
            await context.bot.send_message(
                chat_id=target,
                text=caption,
                parse_mode='HTML'
            )
            continue

        if article.image.desc == SELF_MADE_IMAGE_CASE:
            photo = get_img_buf_by_text(article.title)  # self-made photo
        else:
            photo = article.image.desc  # file_id или URL

        if article.image.is_animation:
            msg = await context.bot.send_animation(
                chat_id=target,
                animation=photo,
                caption=caption,
                parse_mode='HTML'
            )
            file_id = msg.animation.file_id
        else:
            msg = await context.bot.send_photo(
                chat_id=target,
                photo=photo,
                caption=caption,
                parse_mode='HTML'
            )
            file_id = msg.photo[-1].file_id

        if article.image.desc != file_id:
            article.image.desc = file_id
            await update_image_desc(article.link, file_id)


# =========================
# GET ARTICLE
# =========================
async def get_ctx_req_by_config(config: Config, use_cache=True) -> ArticleContextRequest:
    if not config.WIKI_URL_OR_NAME:
        raise Exception(
            f'This option is not supported for this language ({config.LANG_CODE}),\n'
            f'please use TRANSLATIONS[lang][TKey.MAIN_PAGE] instead (or update i18n.py file)'
        )

    ctx = ArticleContext(
        lang=config.LANG_CODE,
        url_or_title=config.WIKI_URL_OR_NAME,
        with_image=config.WITH_IMAGE,
        cached=False,
    )

    url_start = get_quote_url_by_context(ctx)
    if not use_cache:
        return ArticleContextRequest(ctx, url_start, False)

    url_final = await get_cached_final_url(url_start)
    if not url_final or not await article_cached(url_final):
        return ArticleContextRequest(ctx, url_start, False)

    ctx.cached = True
    return ArticleContextRequest(ctx, url_final, True)


async def get_article(
        config: Config,
        *,
        ctx_req: ArticleContextRequest = None,
) -> tuple[Article | None, ArticleContext]:
    if not ctx_req:
        ctx_req = await get_ctx_req_by_config(config, use_cache=config.USE_CACHE_FOR_GETTING_CONTEXT_REQ)

    ctx, url, cached = ctx_req.ctx, ctx_req.url, ctx_req.cached

    last_title = ''
    if config.USE_AND_UPDATE_LAST_FEATURED_TITLE:
        last_title = await get_last_article(config.LANG_CODE)

    if cached:
        article = await get_article_from_db(url, ctx.with_image)

        if article.title == last_title:
            return None, ctx

        return article, ctx

    response = get_request(url)

    if response.status_code != 200:
        raise Exception(
            f'Unexpected response code: {response.status_code}\n{response.content}'
        )

    response.encoding = 'utf-8'

    parser = LANG_PARSERS.get(ctx.lang) or LANG_PARSERS['en']
    soup = clean_soup(BeautifulSoup(response.text, 'html.parser'))

    parser_res = parser(soup, unquote_url(response.url), last_title)
    article, netloc, main_block = parser_res.article, parser_res.netloc, parser_res.main_block

    if not article:
        return None, ctx

    if ctx.with_image:
        article.image = (
                get_image_by_tag(netloc, main_block, ctx)
                or empty_self_made_image(ctx)
        )

    article.link = quote_url(article.link)
    url_final = article.link

    is_article_original = await is_article(ctx.lang, url)
    is_article_final = await is_article(ctx.lang, url_final)

    if is_article_final and config.SAVE_ARTICLE_TO_DB:
        await save_article_to_db(article)
        if is_article_original:
            await set_cached_final_url(url, url_final)
        await set_cached_final_url(url_final, url_final)

    if config.USE_AND_UPDATE_LAST_FEATURED_TITLE:
        await update_featured_articles_in_db(ctx.lang, {article.title})

    return article, ctx


# =========================
# RUN
# =========================
async def run(context: ContextTypes.DEFAULT_TYPE, config: Config) -> bool:
    article, ctx = await get_article(config)

    if not article:
        print(ctx.t(TKey.ARTICLE_NOT_CHANGED))
        return False

    await send_to_targets(context, article, config.TELEGRAM_CHANNELS, config.RULES_URL, ctx)

    if config.USE_AND_UPDATE_LAST_FEATURED_TITLE:
        await set_last_article(config.LANG_CODE, article.title)

    print(ctx.t(TKey.NEW_ARTICLE_SELECTED, title=article.title))
    return True


# =========================
# ENTRYPOINT
# =========================
async def runner(async_main_for_bot, is_test: bool):
    await init_db(DB_TEST_NAME if is_test else DB_NAME)

    app = get_app(is_test)

    try:
        await app.initialize()
        await app.start()

        await async_main_for_bot(app)

    finally:
        await app.stop()
        await app.shutdown()
        await close_db()


def async_run(async_main_for_bot, is_test: bool = False):
    asyncio.run(runner(async_main_for_bot, is_test))
