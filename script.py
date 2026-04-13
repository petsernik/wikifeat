import os
from time import sleep

from config import Config, TMP_FOLDER_PATH
from core import run
from i18n import TRANSLATIONS, TKey


def main():
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)
    lang = 'ru'
    cfg = Config(
        TELEGRAM_CHANNELS=["@wikifeat"],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=TRANSLATIONS[lang][TKey.TODAY_TEMPLATE],
        LANG_CODE=lang,
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, "last_article.txt"),
        WITH_IMAGE=True,
    )
    if not run(cfg):
        return

    sleep(1)

    cfg_text = Config(
        TELEGRAM_CHANNELS=["@wikifeattexts"],
        RULES_URL="https://t.me/wikifeattexts/3",
        WIKI_URL_OR_NAME=TRANSLATIONS[lang][TKey.TODAY_TEMPLATE],
        LANG_CODE=lang,
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, "last_article_only_text.txt"),
        WITH_IMAGE=False,
    )
    run(cfg_text)


if __name__ == "__main__":
    main()
