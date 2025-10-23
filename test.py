from config import Config
from core import main

if __name__ == '__main__':
    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeattest'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://ru.wikipedia.org/wiki/Портрет_П._И._Чайковского',
        LAST_ARTICLE_FILE='last_article_test.txt',
    )
    main(cfg)
