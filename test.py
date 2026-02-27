import os
from time import sleep

from config import Config, TMP_FOLDER_PATH
from core import run

if __name__ == '__main__':
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)

    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeattest'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://web.archive.org/web/20260226234921/https://ru.wikipedia.org/wiki/Заглавная_страница',
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, 'last_article_test.txt'),
        WITH_IMAGE=True,
    )
    run(cfg)
