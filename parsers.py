from typing import Optional, Tuple, Callable

from bs4 import BeautifulSoup, Tag

from config import User_Agent
from models import Article
from utils import get_quote_url_by_tag, get_paragraphs, filter_soup, split_url, quote_url

ParseResult = Tuple[Optional[Article], Optional[str], Optional[Tag]]
NONE_RESULT: ParseResult = (None, None, None)


# =========================
# HELPERS
# =========================
def _clean_last_paragraph(paragraphs: list[str], *suffixes: str) -> None:
    if not paragraphs:
        return

    p = paragraphs[-1].replace('\xa0', ' ')
    for suffix in suffixes:
        if suffix:
            p = p.removesuffix(suffix)

    paragraphs[-1] = p


def _unexpected(lang: str):
    print(f"Unexpected parse case ({lang})")


# =========================
# DEFAULT PARSER
# =========================
def parse_default(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    main_block = soup.find('div', id='mw-content-text')
    title_tag = soup.find('h1', id='firstHeading')

    if not main_block or not title_tag:
        return NONE_RESULT

    title = title_tag.get_text().strip()
    netloc, _ = split_url(url)

    if title == last_title:
        return NONE_RESULT

    paragraphs = get_paragraphs(main_block)
    paragraphs = [p.replace('➤', '') for p in paragraphs]

    article = Article(
        title=title,
        paragraphs=paragraphs,
        link=quote_url(url),
        image=None,
    )

    return article, netloc, main_block


# =========================
# UNIVERSAL FEATURED PARSER
# =========================
def parse_featured(
        soup: BeautifulSoup,
        url: str,
        last_title: str,
        *,
        path_suffixes: tuple[str, ...],
        get_main_block: Callable[[BeautifulSoup], Optional[Tag]],
        get_link_tag: Callable[[Tag], Optional[Tag]],
        clean_suffixes: tuple[str, ...] = (),
        preprocess_block: Optional[Callable[[Tag], Tag]] = None,
        lang: str = "generic",
) -> ParseResult:
    netloc, path = split_url(url)

    if not any(path.endswith(suffix) for suffix in path_suffixes):
        return parse_default(soup, url, last_title)

    main_block = get_main_block(soup)

    if preprocess_block and main_block:
        main_block = preprocess_block(main_block)

    if not main_block:
        return NONE_RESULT

    link_tag = get_link_tag(main_block)

    if not link_tag:
        _unexpected(lang)
        return NONE_RESULT

    title = link_tag.get('title')
    if not title or title == last_title:
        return NONE_RESULT

    paragraphs = get_paragraphs(main_block)

    if clean_suffixes:
        _clean_last_paragraph(paragraphs, *clean_suffixes)

    article = Article(
        title=title,
        paragraphs=paragraphs,
        link=get_quote_url_by_tag(netloc, link_tag),
        image=None,
    )

    return article, netloc, main_block


# =========================
# LANGUAGE PARSERS
# =========================

def parse_en(soup, url, last_title):
    return parse_featured(
        soup,
        url,
        last_title,
        path_suffixes=(
            "/wiki/Wikipedia:Today's_featured_article",
            "/wiki/Wikipedia:Today%27s_featured_article",
            "/wiki/Main_Page",
        ),
        get_main_block=lambda s: s.find('div', class_='mp-tfa') or s.find('div', id='mp-tfa'),
        get_link_tag=lambda b: b.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') in ('Full article...', 'more...')
        ),
        clean_suffixes=(' (Full article...)', ' (more...)'),
        lang="en",
    )


def parse_fr(soup, url, last_title):
    return parse_featured(
        soup,
        url,
        last_title,
        path_suffixes=("/wiki/Wikipédia:Accueil_principal",),
        get_main_block=lambda s: s.find('div', class_='accueil_2017_cadre'),
        get_link_tag=lambda b: b.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') == 'Lire la suite'
        ),
        clean_suffixes=('Lire la suite',),
        lang="fr",
    )


def parse_de(soup, url, last_title):
    return parse_featured(
        soup,
        url,
        last_title,
        path_suffixes=("/wiki/Wikipedia:Hauptseite",),
        get_main_block=lambda s: (
            (s.find('div', id='artikel') or Tag())
            .find('div', class_='hauptseite-box-content')
        ),
        get_link_tag=lambda b: b.find('a', rel='mw:WikiLink', href=True),
        clean_suffixes=('Zum Artikel …',),
        lang="de",
    )


def parse_es(soup, url, last_title):
    return parse_featured(
        soup,
        url,
        last_title,
        path_suffixes=('/wiki/Wikipedia:Portada',),
        get_main_block=lambda s: s.find('div', id='mwCA'),
        get_link_tag=lambda b: b.find('a', href=True),
        lang="es",
    )


def parse_it(soup, url, last_title):
    return parse_featured(
        soup,
        url,
        last_title,
        path_suffixes=('/wiki/Pagina_principale',),
        get_main_block=lambda s: (
            (s.find('div', about='#mwt10') or Tag())
            .find('div', class_='itwiki-template-finestrahome-contenuto')
        ),
        get_link_tag=lambda b: b.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') == 'Leggi la voce'
        ),
        clean_suffixes=('Leggi la voce · Tutte le voci in vetrina',),
        lang="it",
    )


def parse_pt(soup, url, last_title):
    return parse_featured(
        soup,
        url,
        last_title,
        path_suffixes=('/wiki/Wikipédia:Página_principal',),
        get_main_block=lambda s: s.find('div', class_='main-page-block-contents'),
        preprocess_block=lambda b: filter_soup(b, remove_kwargs={'id': 'mwDg'}),
        get_link_tag=lambda b: next(
            (
                a for a in b.find_all('a')
                if 'Artigo completo...' in a.get_text(separator=" ", strip=True)
            ),
            None
        ),
        clean_suffixes=(' (Artigo completo...)',),
        lang="pt",
    )


def parse_pl(soup, url, last_title):
    return parse_featured(
        soup,
        url,
        last_title,
        path_suffixes=('/wiki/Wikipedia:Strona_główna',),
        get_main_block=lambda s: s.find('div', id='main-page-featured-article'),
        get_link_tag=lambda b: b.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') == 'Czytaj więcej…'
        ),
        clean_suffixes=(' Czytaj więcej…',),
        lang="pl",
    )


def parse_be(soup, url, last_title):
    return parse_featured(
        soup,
        url,
        last_title,
        path_suffixes=('/wiki/Галоўная_старонка',),
        get_main_block=lambda s: s.find('div', id='main-page-featured-article'),
        get_link_tag=lambda b: b.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') == 'далей…'
        ),
        lang="be",
    )


def parse_kk(soup, url, last_title):
    return parse_featured(
        soup,
        url,
        last_title,
        path_suffixes=('/wiki/Басты_бет',),
        get_main_block=lambda s: s.find('div', id='main-tfa'),
        get_link_tag=lambda b: b.find('a', href=True),
        lang="kk",
    )


# =========================
# RU (оставлен как есть — сложная логика)
# =========================
def parse_ru(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith('/wiki/Шаблон:Текущая_избранная_статья'):
        main_block = soup.find('div', id='mw-content-text')
        main_block = filter_soup(main_block, remove_kwargs={"role": "presentation"}) if main_block else None

        link_tag = None
        if main_block:
            for p in main_block.find_all('p'):
                a = p.find('a', href=True)
                if a:
                    link_tag = a
                    break

        if not link_tag:
            _unexpected("ru")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        article = Article(
            title=title,
            paragraphs=get_paragraphs(main_block),
            link=get_quote_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    if path.endswith('/wiki/Заглавная_страница'):
        main_block = soup.find('div', id='main-tfa')

        link_tag = main_block.find(
            'a',
            href=True,
            title=lambda t: t and not t.startswith('Шаблон:')
        ) if main_block else None

        if not link_tag:
            _unexpected("ru")
            return NONE_RESULT

        block_type = main_block.find('div', class_='main-box-subtitle').get_text().strip()
        title = link_tag.get('title')

        if not title or title == last_title or block_type != 'Избранная статья':
            return NONE_RESULT

        article = Article(
            title=title,
            paragraphs=get_paragraphs(main_block),
            link=get_quote_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


# =========================
# MAP
# =========================
LANG_PARSERS = {
    'ru': parse_ru,
    'en': parse_en,
    'fr': parse_fr,
    'de': parse_de,
    'es': parse_es,
    'it': parse_it,
    'pt': parse_pt,
    'pl': parse_pl,
    'be': parse_be,
    'kk': parse_kk,
}

from typing import Dict
import aiohttp
from bs4 import BeautifulSoup, Tag


# =========================
# COMMON
# =========================

async def fetch_html(url: str) -> str:
    headers = {"User-Agent": User_Agent}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()


def extract_titles(
        root: Tag,
        *,
        skip_prefixes: tuple[str, ...],
        wiki_prefix: str
) -> set[str]:
    titles = set()

    for a in root.find_all("a"):
        title = a.get("title")
        href = a.get("href", "")

        if not title:
            continue

        if not (href.startswith("/wiki/") or href.startswith(f"//{wiki_prefix}/wiki/")):
            continue

        if title.startswith(skip_prefixes):
            continue

        if href.endswith((".png", ".svg", ".jpg")):
            continue

        titles.add(title)

    return titles


# =========================
# SPECIAL CASES
# =========================

def extract_de(soup: BeautifulSoup, skip_prefixes: tuple[str, ...]) -> set[str]:
    tbody = soup.find("tbody", id="mwBA")
    if not tbody:
        raise RuntimeError("tbody mwBA not found")

    skip_ids = {"mwBQ", "mwCQ"}
    titles = set()

    for tr in tbody.find_all("tr"):
        if tr.get("id") in skip_ids:
            continue

        titles |= extract_titles(
            tr,
            skip_prefixes=skip_prefixes,
            wiki_prefix="de.wikipedia.org"
        )

    return titles


def extract_be(soup: BeautifulSoup, skip_prefixes: tuple[str, ...]) -> set[str]:
    root = soup.find("div", class_="mw-content-ltr mw-parser-output")
    if not root:
        raise RuntimeError("root container not found")

    titles = set()

    for li in root.find_all("li"):
        titles |= extract_titles(
            li,
            skip_prefixes=skip_prefixes,
            wiki_prefix="be.wikipedia.org"
        )

    return titles


# =========================
# CONFIG
# =========================

LANG_FINDER_CONFIG: Dict[str, Dict] = {
    "ru": {
        "url": "https://ru.wikipedia.org/wiki/Википедия:Избранные_статьи",
        "finder": lambda soup: soup.find("section", {"aria-labelledby": "Все_избранные_статьи"}),
    },
    "en": {
        "url": "https://en.wikipedia.org/wiki/Wikipedia:Featured_articles",
        "finder": lambda soup: soup.find_all("div", class_="wp-fa-contents")[1],
    },
    "fr": {
        "url": "https://fr.wikipedia.org/wiki/Wikipédia:Contenus_de_qualité",
        "finder": lambda soup: soup.find_all("div", class_="cadre-colore cdq-cadre")[2:-1],
    },
    "de": {
        "url": "https://de.wikipedia.org/wiki/Wikipedia:Exzellente_Artikel",
        "special": extract_de,
    },
    "es": {
        "url": "https://es.wikipedia.org/wiki/Wikipedia:Artículos_destacados",
        "finder": lambda soup: soup.find("table", attrs={"about": "#mwt9"}),
    },
    "it": {
        "url": "https://it.wikipedia.org/wiki/Wikipedia:Vetrina",
        "finder": lambda soup: soup.find("div", class_="itwiki-vetrina", attrs={"id": "mwDg"}),
    },
    "pt": {
        "url": "https://pt.wikipedia.org/wiki/Wikipédia:Artigos_destacados",
        "finder": lambda soup: soup.find_all("table", attrs={"typeof": "mw:Transclusion"})[-1],
    },
    "pl": {
        "url": "https://pl.wikipedia.org/wiki/Wikipedia:Artykuły_na_Medal",
        "finder": lambda soup: soup.find("div", class_="mw-content-ltr mw-parser-output"),
    },
    "be": {
        "url": "https://be.wikipedia.org/wiki/Вікіпедыя:Выдатныя_артыкулы",
        "special": extract_be,
    },
    "kk": {
        "url": "https://kk.wikipedia.org/wiki/Уикипедия:Таңдаулы_мақалалар",
        "finder": lambda soup: soup.find("table", id="mwKQ"),
    },
}


# =========================
# MAIN FETCH
# =========================

async def fetch_featured_titles(lang: str) -> set[str]:
    cfg = LANG_FINDER_CONFIG.get(lang)
    if not cfg:
        raise ValueError(f"Unsupported lang: {lang}")

    skip_prefixes = await get_skip_prefixes(lang)

    html = await fetch_html(cfg["url"])
    soup = BeautifulSoup(html, "html.parser")

    # special cases
    if "special" in cfg:
        return cfg["special"](soup, skip_prefixes)

    root = cfg["finder"](soup)
    if not root:
        raise RuntimeError(f"Container not found (lang={lang})")

    prefix = f"{lang}.wikipedia.org"

    # FR (list of blocks)
    if isinstance(root, list):
        titles = set()
        for block in root:
            titles |= extract_titles(
                block,
                skip_prefixes=skip_prefixes,
                wiki_prefix=prefix
            )
        return titles

    return extract_titles(
        root,
        skip_prefixes=skip_prefixes,
        wiki_prefix=prefix
    )
