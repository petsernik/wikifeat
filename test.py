import os

from config import Config, TMP_FOLDER_PATH
from core import main

if __name__ == '__main__':
    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeattest'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://web.archive.org/web/20260211133638/https://ru.wikipedia.org/wiki/Заглавная_страница',
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, 'last_article_test.txt'),
    )
    main(cfg)
