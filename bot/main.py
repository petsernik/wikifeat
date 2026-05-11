import pkgutil
from importlib import import_module

from telegram.ext import (
    Application,
    MessageHandler,
    filters,
)

import bot.handlers
from bot.handlers.registry import COMMAND_HANDLERS, CALLBACK_HANDLERS
from bot.handlers.text import handle_text
from config import TELEGRAM_BOT_TOKEN
from db import init_db, close_db, has_featured_articles, update_featured_articles_in_db
from i18n import TRANSLATIONS
from parsers import fetch_featured_titles


def load_handlers():
    for module in pkgutil.iter_modules(bot.handlers.__path__):
        if module.name in {"registry", "text"}:
            continue

        import_module(f"bot.handlers.{module.name}")


def register_handlers(app):
    # импортируем модули -> декораторы срабатывают
    load_handlers()

    # регистрируем handlers
    for handler in (*COMMAND_HANDLERS, *CALLBACK_HANDLERS):
        app.add_handler(handler)

    # text router
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # =========================
    # DB INIT
    # =========================
    async def post_init(_: Application):
        await init_db()
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
