from config import Config
from core import main

if __name__ == '__main__':
    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeattest'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://en.wikipedia.org/wiki/Funerary_Monument_to_Sir_John_Hawkwood',
        LAST_ARTICLE_FILE='last_article_test.txt',
    )
    main(cfg)
