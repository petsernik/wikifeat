from typing import Optional, Tuple
from bs4 import BeautifulSoup, Tag

from models import Article
from utils import get_url_by_tag, get_paragraphs, filter_soup, join_url, split_url, normalize_url

ParseResult = Tuple[Optional[Article], Optional[str], Optional[Tag]]
NONE_RESULT: ParseResult = (None, None, None)


def _clean_last_paragraph(paragraphs: list[str], *suffixes: str) -> None:
    if not paragraphs:
        return
    p = paragraphs[-1].replace('\xa0', ' ')
    for suffix in suffixes:
        if suffix:
            p = p.removesuffix(suffix)
    paragraphs[-1] = p


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
        link=url,
        image=None,
    )
    return article, netloc, main_block


def _unexpected(lang: str):
    print(f"Unexpected parse case ({lang})")


def parse_ru(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith('/wiki/Шаблон:Текущая_избранная_статья'):
        main_block = soup.find('div', id='mw-content-text')
        main_block = filter_soup(main_block, remove_kwargs={"role": "presentation"}) if main_block else None
        link_tag = main_block.find('a', href=True) if main_block else None

        if not link_tag:
            _unexpected("ru")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        article = Article(
            title=title,
            paragraphs=get_paragraphs(main_block),
            link=get_url_by_tag(netloc, link_tag),
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
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


def parse_en(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith("/wiki/Wikipedia:Today's_featured_article") or \
            path.endswith("/wiki/Wikipedia:Today%27s_featured_article") or \
            path.endswith("/wiki/Main_Page"):

        main_block = soup.find('div', class_='mp-tfa') or soup.find('div', id='mp-tfa')
        if not main_block:
            return parse_default(soup, url, last_title)

        link_tag = main_block.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') in ('Full article...', 'more...')
        )

        if not link_tag:
            _unexpected("en")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        paragraphs = get_paragraphs(main_block)
        _clean_last_paragraph(paragraphs, ' (Full article...)', ' (more...)')

        article = Article(
            title=title,
            paragraphs=paragraphs,
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


def parse_fr(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith("/wiki/Wikipédia:Accueil_principal"):
        main_block = soup.find('div', class_='accueil_2017_cadre')

        link_tag = main_block.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') == 'Lire la suite'
        ) if main_block else None

        if not link_tag:
            _unexpected("fr")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        paragraphs = get_paragraphs(main_block)
        _clean_last_paragraph(paragraphs, 'Lire la suite')

        article = Article(
            title=title,
            paragraphs=paragraphs,
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


def parse_de(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith("/wiki/Wikipedia:Hauptseite"):
        main_block = soup.find('div', id='artikel')
        main_block = main_block.find('div', class_='hauptseite-box-content') if main_block else None
        link_tag = main_block.find('a', href=True) if main_block else None

        if not link_tag:
            _unexpected("de")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        paragraphs = get_paragraphs(main_block)
        _clean_last_paragraph(paragraphs, 'Zum Artikel …')

        article = Article(
            title=title,
            paragraphs=paragraphs,
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


def parse_es(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith('/wiki/Wikipedia:Portada'):
        main_block = soup.find('div', id='mwCA')
        link_tag = main_block.find('a', href=True) if main_block else None

        if not link_tag:
            _unexpected("es")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        article = Article(
            title=title,
            paragraphs=get_paragraphs(main_block),
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


def parse_it(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith('/wiki/Pagina_principale'):
        main_block = soup.find('div', about='#mwt10')
        main_block = main_block.find(
            'div', class_='itwiki-template-finestrahome-contenuto'
        ) if main_block else None

        link_tag = main_block.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') == 'Leggi la voce'
        ) if main_block else None

        if not link_tag:
            _unexpected("it")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        paragraphs = get_paragraphs(main_block)
        _clean_last_paragraph(paragraphs, 'Leggi la voce · Tutte le voci in vetrina')

        article = Article(
            title=title,
            paragraphs=paragraphs,
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


def parse_pt(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith('/wiki/Wikipédia:Página_principal'):
        main_block = soup.find('div', class_='main-page-block-contents')
        main_block = filter_soup(main_block, remove_kwargs={'id': 'mwDg'}) if main_block else None

        link_tag = next(
            (
                a for a in (main_block.find_all('a') if main_block else [])
                if 'Artigo completo...' in a.get_text(separator=" ", strip=True)
            ),
            None
        )

        if not link_tag:
            _unexpected("pt")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        paragraphs = get_paragraphs(main_block)
        _clean_last_paragraph(paragraphs, ' (Artigo completo...)')

        article = Article(
            title=title,
            paragraphs=paragraphs,
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


def parse_pl(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith('/wiki/Wikipedia:Strona_główna'):
        main_block = soup.find('div', id='main-page-featured-article')

        link_tag = main_block.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') == 'Czytaj więcej…'
        ) if main_block else None

        if not link_tag:
            _unexpected("pl")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        paragraphs = get_paragraphs(main_block)
        _clean_last_paragraph(paragraphs, ' Czytaj więcej…')

        article = Article(
            title=title,
            paragraphs=paragraphs,
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


def parse_be(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith('/wiki/Галоўная_старонка'):
        main_block = soup.find('div', id='main-page-featured-article')

        link_tag = main_block.find(
            'a',
            string=lambda s: s and s.strip().replace('\xa0', ' ') == 'далей…'
        ) if main_block else None

        if not link_tag:
            _unexpected("be")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        paragraphs = get_paragraphs(main_block)
        if paragraphs:
            p = paragraphs[-1].replace('\xa0', ' ')
            paragraphs[-1] = p.replace(' (далей…).', '.')

        article = Article(
            title=title,
            paragraphs=paragraphs,
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


def parse_kk(soup: BeautifulSoup, url: str, last_title: str) -> ParseResult:
    netloc, path = split_url(url)

    if path.endswith('/wiki/Басты_бет'):
        main_block = soup.find('div', id='main-tfa')
        link_tag = main_block.find('a', href=True) if main_block else None

        if not link_tag:
            _unexpected("kk")
            return NONE_RESULT

        title = link_tag.get('title')
        if not title or title == last_title:
            return NONE_RESULT

        article = Article(
            title=title,
            paragraphs=get_paragraphs(main_block),
            link=get_url_by_tag(netloc, link_tag),
            image=None,
        )
        return article, netloc, main_block

    return parse_default(soup, url, last_title)


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
