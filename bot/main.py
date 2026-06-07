import asyncio
import sys

from telegram.error import TimedOut, NetworkError
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from bot.handlers.registry import get_handlers
from bot.handlers.text import handle_text
from constants import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_TEST_TOKEN, DB_NAME, DB_TEST_NAME
from db import init_db, close_db, has_featured_articles, update_featured_articles_in_db
from i18n import TRANSLATIONS
from parsers import fetch_featured_titles


def register_handlers(app):
    # регистрируем handlers
    for handler in get_handlers():
        app.add_handler(handler)

    # text router
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


class LimitedHTTPXRequest(HTTPXRequest):
    def __init__(self, *args, max_concurrent, **kwargs):
        super().__init__(*args, **kwargs)
        self._sem = asyncio.Semaphore(max_concurrent)

    async def do_request(self, *args, **kwargs):
        async with self._sem:
            for delay in (1, 2, 5):
                try:
                    return await asyncio.wait_for(
                        super().do_request(*args, **kwargs),
                        timeout=15
                    )

                except (TimedOut, NetworkError) as exc:
                    last_exc = exc
                    await asyncio.sleep(delay)

                except asyncio.TimeoutError:
                    last_exc = TimeoutError("HTTP request stuck")
                    await asyncio.sleep(delay)

            raise last_exc


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

    request = LimitedHTTPXRequest(
        connection_pool_size=100,
        read_timeout=10,
        write_timeout=10,
        connect_timeout=10,
        pool_timeout=5,
        max_concurrent=40,
    )

    get_updates_request = LimitedHTTPXRequest(
        connection_pool_size=10,
        pool_timeout=30,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        max_concurrent=2,
    )

    app = (Application.builder()
           .token(token)
           .arbitrary_callback_data(True)
           .request(request)
           .get_updates_request(get_updates_request)
           .build())

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
