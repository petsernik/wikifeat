import os
from time import sleep

from config import Config, TMP_FOLDER_PATH
from core import main

if __name__ == '__main__':
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)

    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeat'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://ru.wikipedia.org/wiki/Шаблон:Текущая_избранная_статья',
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, 'last_article.txt'),
    )
    main(cfg)

    sleep(1)

    cfg_text = Config(
        TELEGRAM_CHANNELS=['@wikifeattexts'],
        RULES_URL='https://t.me/wikifeattexts/3',
        WIKI_URL='https://ru.wikipedia.org/wiki/Шаблон:Текущая_избранная_статья',
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, 'last_article_only_text.txt'),
    )
    main(cfg_text, with_image=False)
