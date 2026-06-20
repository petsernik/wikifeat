import asyncio
import contextlib
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
    last_restart = 0.0

    while True:
        await asyncio.sleep(WATCHDOG_SLEEP_TIME)

        now = time.monotonic()

        request = app.bot_data["bot_request"]
        polling_request = app.bot_data["polling_request"]

        bot_dead = now - request.last_success > DEAD_TIMEOUT
        polling_dead = now - polling_request.last_success > DEAD_TIMEOUT

        if not (bot_dead and polling_dead):
            continue

        # 🔒 анти-спам рестартов
        if now - last_restart < RESTART_COOLDOWN:
            continue

        logger.warning("[WATCHDOG] watchdog triggered: bot_dead and polling_dead, resetting HTTP layer")

        try:
            await reset_http_layer(app)

            last_restart = time.monotonic()

            logger.warning("[WATCHDOG] watchdog: HTTP layer reset successful")

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

    async def post_init(_: Application):
        logger.info("[INIT] starting application initialization")

        await init_db(DB_TEST_NAME if is_test else DB_NAME)
        logger.info("[INIT] database initialized")

        task = asyncio.create_task(watchdog(app))
        app.bot_data["watchdog_task"] = task
        logger.info("[INIT] watchdog task started")

        for lang in TRANSLATIONS.keys():
            try:
                logger.info("[INIT] processing featured articles for lang=%s", lang)

                if await has_featured_articles(lang):
                    logger.info("[INIT] skip lang=%s (already exists)", lang)
                    continue

                titles = await fetch_featured_titles(lang)

                if not titles:
                    logger.warning("[INIT] no titles for lang=%s", lang)
                    continue

                await update_featured_articles_in_db(lang, titles)
                logger.info("[INIT] updated featured articles for lang=%s", lang)

            except Exception as exc:
                logger.exception("[INIT] error lang=%s: %s", lang, exc)

        logger.info("[INIT] completed successfully")

    async def post_shutdown(_: Application):
        logger.info("[SHUTDOWN] starting application shutdown")

        await close_db()
        logger.info("[SHUTDOWN] database closed")

        task = app.bot_data.get("watchdog_task")

        if task:
            logger.info("[SHUTDOWN] cancelling watchdog task")
            task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await task

            logger.info("[SHUTDOWN] watchdog stopped")

        req = app.bot_data["bot_request"]
        poll = app.bot_data["polling_request"]

        logger.info("[SHUTDOWN] shutting down HTTP layer")

        await req.shutdown()
        await poll.shutdown()

        logger.info("[SHUTDOWN] completed successfully")

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
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger.setLevel(logging.INFO)

    main()
