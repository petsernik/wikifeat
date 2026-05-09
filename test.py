import asyncio
from types import SimpleNamespace
from typing import Iterable

from telegram.ext import Application

from config import Config
from core import run, async_run
from db import delete_url, get_pool
from filter import get_skip_prefixes
from i18n import TRANSLATIONS, TKey, ADDITIONAL_TRANSLATIONS


# =========================
# BASE TEST RUNNER
# =========================
async def _test_page(app: Application, lang: str, url_or_name: str, with_image: bool = True):
    ctx = SimpleNamespace(bot=app.bot)

    cfg = Config(
        TELEGRAM_CHANNELS=["@wikifeattest"],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=url_or_name,
        LANG_CODE=lang,
        USE_AND_UPDATE_LAST_FEATURED_TITLE=False,
        WITH_IMAGE=with_image,
    )

    await run(ctx, cfg)
    await asyncio.sleep(1)


# =========================
# BY KEY
# =========================
async def _test_page_by_key(app: Application, lang: str, key: TKey, with_image: bool = True):
    await _test_page(app, lang, TRANSLATIONS[lang][key], with_image)
    await asyncio.sleep(1)


# =========================
# PRESET TESTS
# =========================
async def _test_today_template(app: Application, lang: str, with_image: bool = True):
    await _test_page_by_key(app, lang, TKey.TODAY_TEMPLATE, with_image)


async def _test_main_page(app: Application, lang: str, with_image: bool = True):
    await _test_page_by_key(app, lang, TKey.MAIN_PAGE, with_image)


async def _test_random_page(app: Application, lang: str, with_image: bool = True):
    await _test_page_by_key(app, lang, TKey.RANDOM_FEATURED_PAGE, with_image)


# =========================
# ITERABLE TESTS
# =========================
async def _test_today_templates_by_iterable(app: Application, languages: Iterable[str], with_image: bool = True):
    for lang in languages:
        await _test_today_template(app, lang, with_image)


async def _test_main_pages_by_iterable(app: Application, languages: Iterable[str], with_image: bool = True):
    for lang in languages:
        await _test_main_page(app, lang, with_image)


async def _test_random_pages_by_iterable(app: Application, languages: Iterable[str], with_image: bool = True):
    for lang in languages:
        await _test_random_page(app, lang, with_image)


async def _cleanup_by_prefix(lang: str, prefix: str):
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            # articles_cache
            await conn.execute(
                """
                DELETE FROM articles_cache
                WHERE title LIKE $1
                """,
                f"{prefix}%"
            )

            # featured_articles
            await conn.execute(
                """
                DELETE FROM featured_articles
                WHERE lang = $1 AND title LIKE $2
                """,
                lang,
                f"{prefix}%"
            )

            # last_featured_articles
            await conn.execute(
                """
                DELETE FROM last_featured_articles
                WHERE lang = $1 AND title LIKE $2
                """,
                lang,
                f"{prefix}%"
            )


async def cleanup_reserved_pages():
    for lang, tr in ADDITIONAL_TRANSLATIONS.items():

        # =========================
        # 1. i18n страницы
        # =========================
        main_page = tr.get(TKey.MAIN_PAGE)
        today_page = tr.get(TKey.TODAY_TEMPLATE)

        if main_page:
            await delete_url(lang, main_page)

        if today_page:
            await delete_url(lang, today_page)

        # =========================
        # 2. namespace cleanup
        # =========================
        prefixes = await get_skip_prefixes(lang)

        for prefix in prefixes:
            await _cleanup_by_prefix(lang, prefix)


# =========================
# MAIN
# =========================
async def main(app: Application):
    # ===== TEST CASES =====
    # await _test_main_page(app, "fr", True)
    # await _test_main_page(app, "es", True)
    # await cleanup_reserved_pages()
    # await _test_main_page(app, "ru", False)
    # await _test_page(app, 'ru', 'Голова', True)
    # ====== TEST UPDATING FEATURED ALL ======
    # for lang in TRANSLATIONS.keys():
    #     try:
    #         await update_featured_articles_in_db(lang, await fetch_featured_titles(lang))
    #     except Exception as exc:
    #         print(exc)
    await delete_url('ru', 'Обмен')


if __name__ == "__main__":
    async_run(main)
