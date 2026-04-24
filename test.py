import os
from time import sleep
from typing import Iterable

from config import Config, TMP_FOLDER_PATH
from core import run
from i18n import TRANSLATIONS, TKey


def _test_page(lang: str, url_or_name: str):
    cfg = Config(
        TELEGRAM_CHANNELS=["@wikifeattest"],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=url_or_name,
        LANG_CODE=lang,
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, "last_article_test.txt"),
        WITH_IMAGE=True,
    )
    run(cfg)
    sleep(1)


def _test_page_by_key(lang: str, key: TKey):
    _test_page(lang, TRANSLATIONS[lang][key])
    sleep(1)


def _test_today_template(lang: str):
    _test_page_by_key(lang, TKey.TODAY_TEMPLATE)


def _test_main_page(lang: str):
    _test_page_by_key(lang, TKey.MAIN_PAGE)


def _test_today_templates_by_iterable(languages: Iterable[str]):
    for lang in languages:
        _test_today_template(lang)


def _test_main_pages_by_iterable(languages: Iterable[str]):
    for lang in languages:
        _test_main_page(lang)


def _test_today_templates():
    _test_today_templates_by_iterable(TRANSLATIONS.keys()) # not yet supported


def _test_main_pages():
    _test_main_pages_by_iterable(TRANSLATIONS.keys())


def _test_random_page(lang: str):
    _test_page_by_key(lang, TKey.RANDOM_FEATURED_PAGE)


def _test_random_pages_by_iterable(languages: Iterable[str]):
    for lang in languages:
        _test_random_page(lang)


def _test_random_pages():
    _test_random_pages_by_iterable(TRANSLATIONS.keys())


if __name__ == "__main__":
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)

    _test_today_template('ru')
    _test_today_template('en')
    # _test_main_page('ru')
    # _test_main_pages()
    # _test_random_pages_by_iterable(['fr'])
    _test_page('ru', 'Рукопись покойного Клементия Акимовича Хабарова')
    _test_page('ru', 'Солнце')
    _test_page('ru', 'Эссекс (королевство)')
