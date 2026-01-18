from config import Config
from core import main

if __name__ == '__main__':
    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeattest'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://web.archive.org/web/20251118154458/https://es.wikipedia.org/wiki/Obra_derivada',
        LAST_ARTICLE_FILE='last_article_test.txt',
    )
    main(cfg)
    cfg = Config(
        TELEGRAM_CHANNELS=['@wikifeattest'],
        RULES_URL='https://t.me/wikifeat/4',
        WIKI_URL='https://web.archive.org/web/20260110125615/https://en.wikipedia.org/wiki/Aguas_Calientes,_Peru',
        LAST_ARTICLE_FILE='last_article_test.txt',
    )
    main(cfg)
