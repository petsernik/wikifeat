import os
from time import sleep

from config import Config, TMP_FOLDER_PATH
from core import run

if __name__ == '__main__':
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)

    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeattest'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://hu.wikipedia.org/wiki/Super_Mario_Bros.:_A_film',
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, 'last_article_test.txt'),
        WITH_IMAGE=True,
    )
    run(cfg)

    sleep(1)

    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeattest'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://de.wikipedia.org/wiki/Florida',
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, 'last_article_test.txt'),
        WITH_IMAGE=True,
    )
    run(cfg)
