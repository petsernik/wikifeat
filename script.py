from types import SimpleNamespace

from telegram.ext import Application

from config import Config
from core import run, async_run
from i18n import TRANSLATIONS, TKey


# =========================
# MAIN LOGIC
# =========================
async def main(app: Application):
    lang = "ru"

    ctx = SimpleNamespace(bot=app.bot)

    # =========================
    # FIRST (images)
    # =========================
    cfg = Config(
        TELEGRAM_CHANNELS=["@wikifeat"],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=TRANSLATIONS[lang][TKey.TODAY_TEMPLATE],
        LANG_CODE=lang,
        USE_AND_UPDATE_LAST_FEATURED_TITLE=True,
        WITH_IMAGE=True,
    )

    ok = await run(ctx, cfg)
    if not ok:
        return

    # =========================
    # SECOND (text only)
    # =========================
    cfg_text = Config(
        TELEGRAM_CHANNELS=["@wikifeattexts"],
        RULES_URL="https://t.me/wikifeattexts/3",
        WIKI_URL_OR_NAME=TRANSLATIONS[lang][TKey.TODAY_TEMPLATE],
        LANG_CODE=lang,
        USE_AND_UPDATE_LAST_FEATURED_TITLE=False,
        WITH_IMAGE=False,
    )

    await run(ctx, cfg_text)


if __name__ == "__main__":
    async_run(main)
