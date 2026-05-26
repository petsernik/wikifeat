import sys

from telegram.ext import (
    Application,
    MessageHandler,
    filters,
)

from bot.handlers.registry import get_handlers
from bot.handlers.text import handle_text
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_TEST_TOKEN, DB_NAME, DB_TEST_NAME
from db import init_db, close_db, has_featured_articles, update_featured_articles_in_db
from i18n import TRANSLATIONS
from parsers import fetch_featured_titles


def register_handlers(app):
    # регистрируем handlers
    for handler in get_handlers():
        app.add_handler(handler)

    # text router
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# =========================
# MAIN
# =========================
def main():
    is_test = "--test" in sys.argv

    token = (
        TELEGRAM_BOT_TEST_TOKEN
        if is_test
        else TELEGRAM_BOT_TOKEN
    )

    app = Application.builder().token(token).build()

    # =========================
    # DB INIT
    # =========================
    async def post_init(_: Application):
        await init_db(DB_TEST_NAME if is_test else DB_NAME)

        for lang in TRANSLATIONS.keys():
            try:
                if await has_featured_articles(lang):
                    continue

                titles = await fetch_featured_titles(lang)

                if not titles:
                    continue

                await update_featured_articles_in_db(lang, titles)

            except Exception as exc:
                print(f"[featured init error] lang={lang}: {exc}")

    async def post_shutdown(_: Application):
        await close_db()

    app.post_init = post_init
    app.post_shutdown = post_shutdown

    register_handlers(app)

    # =========================
    # RUN
    # =========================
    app.run_polling()


# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    main()
