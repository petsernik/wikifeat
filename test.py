import os

from config import Config, TMP_FOLDER_PATH
from core import run

if __name__ == '__main__':
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)

    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeattest'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://en.wikipedia.org/wiki/Wikipedia:Today%27s_featured_article',
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, 'last_article_test.txt'),
        WITH_IMAGE=True,
    )
    run(cfg)
