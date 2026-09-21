import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from constants import SELF_MADE_IMAGE_CASE, NAZI_IMAGE_CASE
from i18n import TKey, is_unknown_author
from models import Image, ArticleContext
from utils import (
    get_request,
    get_quote_url_by_tag,
    extract_attrs_info,
    html_to_text,
    replace_links_with_numbers,
    update_links,
    has_link,
)


# =========================
# IMAGE BY TAG
# =========================
def get_image_by_tag(
        netloc: str,
        main_block: Tag,
        ctx: ArticleContext,
) -> Image:
    img_tag = main_block.select_one('a[href] img')

    if not img_tag:
        return pre_image_by_text(ctx, SELF_MADE_IMAGE_CASE)

    image_page_url = get_quote_url_by_tag(netloc, img_tag)
    return get_image_by_link(image_page_url, ctx)


# =========================
# IMAGE BY LINK
# =========================
def get_image_by_link(
        image_page_url: str,
        ctx: ArticleContext,
) -> Image:
    if (
            image_page_url.endswith(":Commons-logo.svg")
            and ctx.url_or_title != ctx.t(TKey.WIKIMEDIA_COMMONS_TITLE)
    ):
        return pre_image_by_text(ctx, SELF_MADE_IMAGE_CASE)

    netloc = urlparse(image_page_url).netloc
    response = get_request(image_page_url)

    if response.status_code in (404, 429):
        return pre_image_by_text(ctx, SELF_MADE_IMAGE_CASE)

    if response.status_code != 200:
        raise Exception(
            f'Unexpected response code when get image page: '
            f'{response.status_code}\n'
            f'Response body: {response.content}'
        )

    image_soup = BeautifulSoup(response.text, 'html.parser')

    # nazi image case
    nazi_img = image_soup.find('img', alt='Nazi symbol')
    if nazi_img:
        return pre_image_by_text(ctx, NAZI_IMAGE_CASE)

    image_url = None
    width_max, height_max = 2000, 2000

    resolutions_span = image_soup.find(
        'span',
        class_='mw-filepage-other-resolutions',
    )

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

    if (
            not image_url
            or image_url.startswith(
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/'
        'OOjs_UI_icon_edit-ltr-progressive.svg/'
    )
    ):
        return pre_image_by_text(ctx, SELF_MADE_IMAGE_CASE)

    raw_licenses = {
        re.sub(r'\s+', ' ', tag.get_text(strip=True))
        for tag in image_soup.find_all(
            class_=re.compile('licensetpl_short')
        )
    }

    if not raw_licenses:
        return pre_image_by_text(ctx, SELF_MADE_IMAGE_CASE)

    fair_use_keywords = {
        ctx.t(TKey.FAIR_USE),
        "Fair use",
    }

    if ctx.lang == 'fr':
        fair_use_keywords.add("marque déposée")

    if not raw_licenses.isdisjoint(fair_use_keywords):
        return pre_image_by_text(ctx, SELF_MADE_IMAGE_CASE)

    replacements = {
        "CC BY-SA 4.0": "CC BY-SA",
        "CC BY 4.0": "CC BY",
    }

    image_licenses = {
        replacements.get(lic, lic)
        for lic in raw_licenses
    }

    cc0 = "CC0"
    pdm = ctx.t(TKey.PUBLIC_DOMAIN)

    pd_licenses_map = {
        "Public domain": pdm,
        "PDM": pdm,
        "CC0": cc0,
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
            return pre_image_by_text(ctx, SELF_MADE_IMAGE_CASE)

        image_url = req.url

    image_author_html = extract_attrs_info(
        image_soup,
        find_kwargs={'class': 'licensetpl_attr'},
        next_tags=None,
    )

    if image_author_html and "Diego Delso" in image_author_html:
        image_author_html = image_author_html.replace(
            "Diego Delso",
            'Diego Delso, '
            '<a href="https://delso.photo">delso.photo</a>',
        )

    if not image_author_html:
        image_author_html = extract_attrs_info(
            image_soup,
            find_kwargs={'id': 'fileinfotpl_aut'},
            next_tags=('td', 'th'),
        )

    source_html = extract_attrs_info(
        image_soup,
        find_kwargs={'id': 'fileinfotpl_src'},
        next_tags=('td', 'th'),
    )

    if not source_html:
        return pre_image_by_text(ctx, SELF_MADE_IMAGE_CASE)

    unknown = False

    if image_author_html:
        image_author_text = html_to_text(image_author_html)
        unknown = is_unknown_author(image_author_text)

        if not unknown:
            if not has_link(image_author_html):
                source_soup = BeautifulSoup(
                    source_html,
                    'html.parser',
                )
                links = source_soup.find_all('a', href=True)

                if len(links) == 1:
                    href = links[0].get('href')
                    image_author_html = (
                        f'<a href="{href}">{image_author_html}</a>'
                    )

            if ',' in image_author_text or ';' in image_author_text:
                image_author_html = ctx.t(
                    TKey.AUTHOR_MULTIPLE,
                    author=image_author_html,
                )
            else:
                image_author_html = ctx.t(
                    TKey.AUTHOR_SINGLE,
                    author=image_author_html,
                )

    if unknown or not image_author_html:
        source_html = replace_links_with_numbers(source_html)
        source_text = html_to_text(source_html)

        if ',' in source_text or ';' in source_text:
            source_html = ctx.t(
                TKey.SOURCE_MULTIPLE,
                source=source_html,
            )
        else:
            source_html = ctx.t(
                TKey.SOURCE_SINGLE,
                source=source_html,
            )

        image_author_html = (
            f"{ctx.t(TKey.AUTHOR_UNKNOWN)}, {source_html}"
        )

    image_author_html = update_links(
        netloc,
        image_author_html,
    )

    return Image(
        desc=image_url,
        licenses=sorted(image_licenses),
        page_url=image_page_url,
        author_html=image_author_html,
        is_animation=image_url.endswith(".gif"),
    )


# =========================
# IMAGE BY TEXT
# =========================
def pre_image_by_text(
        ctx: ArticleContext,
        desc: str,
) -> Image:
    return Image(
        desc=desc,
        licenses=['CC0'],
        page_url='https://typodermicfonts.com/public-domain/',
        author_html=ctx.t(
            TKey.FONTS_AUTHOR,
            author='Ray Larabie',
        ),
        is_animation=False,
    )
