import os

from config import Config, TMP_FOLDER_PATH
from core import run, get_image_by_link, send_to_telegram
from i18n import TRANSLATIONS, TKey
from models import Article

if __name__ == "__main__":
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)

    lang = "kk"
    cfg = Config(
        TELEGRAM_CHANNELS=["@wikifeattest"],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=TRANSLATIONS[lang][TKey.MAIN_PAGE],
        LANG_CODE=lang,
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, "last_article_test.txt"),
        WITH_IMAGE=True,
    )
    run(cfg)

    # image = get_image_by_link(
    #     "https://commons.wikimedia.org/wiki/File:Devushka_by_Konenkov_(1914,_Tretyakov_gallery)_01_by_shakko.JPG"
    # )
    # article = Article(
    #     'Лезвие бритвы (роман)',
    #     [
    #         '(Далее описание фото) Сергей Конёнков. Девушка. 1914 год. Государственная Третьяковская галерея. '
    #         'Из дерева была изваяна статуя Анны в полтора человеческих роста, описанная в романе. '
    #         'Также в романе упоминается, что фигура, такая же, как у статуи Конёнкова, была у Симы Металиной.'
    #     ],
    #     cfg.WIKI_URL,
    #     image)
    # send_to_telegram(article, cfg.TELEGRAM_CHANNELS, cfg.RULES_URL)
