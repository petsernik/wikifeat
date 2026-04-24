import os
from time import sleep
from typing import Iterable

from config import Config, TMP_FOLDER_PATH
from core import run
from i18n import TRANSLATIONS, TKey


def _test_page(lang: str, url_or_name: str, with_image: bool):
    cfg = Config(
        TELEGRAM_CHANNELS=["@wikifeattest"],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=url_or_name,
        LANG_CODE=lang,
        LAST_ARTICLE_FILE='',
        WITH_IMAGE=with_image,
    )
    run(cfg)
    sleep(1)


def _test_page_by_key(lang: str, key: TKey, with_image: bool = True):
    _test_page(lang, TRANSLATIONS[lang][key], with_image)
    sleep(1)


def _test_today_template(lang: str, with_image: bool = True):
    _test_page_by_key(lang, TKey.TODAY_TEMPLATE, with_image)


def _test_main_page(lang: str, with_image: bool = True):
    _test_page_by_key(lang, TKey.MAIN_PAGE, with_image)


def _test_today_templates_by_iterable(languages: Iterable[str], with_image: bool = True):
    for lang in languages:
        _test_today_template(lang, with_image)


def _test_main_pages_by_iterable(languages: Iterable[str], with_image: bool = True):
    for lang in languages:
        _test_main_page(lang, with_image)


def _test_today_templates(with_image: bool = True):
    _test_today_templates_by_iterable(TRANSLATIONS.keys(), with_image)


def _test_main_pages(with_image: bool = True):
    _test_main_pages_by_iterable(TRANSLATIONS.keys(), with_image)


def _test_random_page(lang: str, with_image: bool = True):
    _test_page_by_key(lang, TKey.RANDOM_FEATURED_PAGE, with_image)


def _test_random_pages_by_iterable(languages: Iterable[str], with_image: bool = True):
    for lang in languages:
        _test_random_page(lang, with_image)


def _test_random_pages(with_image=True):
    _test_random_pages_by_iterable(TRANSLATIONS.keys(), with_image)


if __name__ == "__main__":
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)

    # _test_today_template('ru')
    # _test_today_template('en')
    _test_main_page('ru')
    # _test_main_pages()
    # _test_random_pages_by_iterable(['fr'])
    # _test_page('ru', 'Портрет Текумсе')

    # _test_page('ru', 'Солнце')
    # _test_page('ru', 'Эссекс (королевство)')
