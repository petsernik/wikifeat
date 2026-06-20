import asyncio
import logging
import sys
import time

from telegram.ext import (
    Application,
    MessageHandler,
    filters,
)

from bot.handlers.registry import get_handlers
from bot.handlers.text import handle_text
from constants import DB_NAME, DB_TEST_NAME, WATCHDOG_SLEEP_TIME, DEAD_TIMEOUT, RESTART_COOLDOWN
from db import init_db, close_db, has_featured_articles, update_featured_articles_in_db
from i18n import TRANSLATIONS
from models import get_app
from parsers import fetch_featured_titles

logger = logging.getLogger(__name__)


async def safe_call(coro, timeout, name):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except Exception:
        logger.exception("watchdog: %s failed", name)
        return None


async def reset_http_layer(app: Application):
    request = app.bot_data["bot_request"]
    polling_request = app.bot_data["polling_request"]

    # мягкий сброс HTTP соединений
    await safe_call(request.shutdown(), 15, "bot_request.shutdown")
    await safe_call(polling_request.shutdown(), 15, "polling_request.shutdown")

    await safe_call(request.initialize(), 15, "bot_request.initialize")
    await safe_call(polling_request.initialize(), 15, "polling_request.initialize")

    # reset metrics
    ts = time.monotonic()
    request.last_success = ts
    polling_request.last_success = ts


async def watchdog(app: Application):
    last_restart = 0

    while True:
        await asyncio.sleep(WATCHDOG_SLEEP_TIME)

        now = time.monotonic()

        request = app.bot_data["bot_request"]
        polling_request = app.bot_data["polling_request"]

        bot_dead = now - request.last_success > DEAD_TIMEOUT
        polling_dead = now - polling_request.last_success > DEAD_TIMEOUT

        if not (bot_dead or polling_dead):
            continue

        # 🔒 анти-спам рестартов
        if now - last_restart < RESTART_COOLDOWN:
            continue

        logger.warning(
            "watchdog triggered: bot_dead=%s polling_dead=%s",
            bot_dead,
            polling_dead,
        )

        try:
            await reset_http_layer(app)

            last_restart = time.monotonic()

            logger.warning("watchdog: HTTP layer reset successful")

        except Exception:
            logger.exception("watchdog failed completely")


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

    app = get_app(is_test)

    # =========================
    # DB INIT
    # =========================
    async def post_init(_: Application):
        await init_db(DB_TEST_NAME if is_test else DB_NAME)

        app.create_task(watchdog(app))

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
