import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

from telegram.ext import Application

from constants import BOT_PROCESS_NAME, ENSURE_BOT_RUNNING
from db import get_process_heartbeat, delete_process_heartbeat
from i18n import TRANSLATIONS, TKey
from models import Config
from parse import run, async_run
from utils import terminate_process


# =========================
# MAIN LOGIC
# =========================
async def main(app: Application):
    if ENSURE_BOT_RUNNING:
        await ensure_bot_running()

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
        WITH_IMAGE=True,
        USE_AND_UPDATE_LAST_FEATURED_TITLE=True,
        SAVE_ARTICLE_TO_DB=True,
        USE_CACHE_FOR_GETTING_CONTEXT_REQ=False
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
        WITH_IMAGE=False,
        USE_AND_UPDATE_LAST_FEATURED_TITLE=False,
        SAVE_ARTICLE_TO_DB=False,
        USE_CACHE_FOR_GETTING_CONTEXT_REQ=False
    )

    await run(ctx, cfg_text)


def start_bot():
    creation_flags = 0

    if os.name == "nt":
        creation_flags = (
            subprocess.CREATE_NO_WINDOW
            | subprocess.CREATE_NEW_PROCESS_GROUP
        )

    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "bot.main",
        ],
        creationflags=creation_flags,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )


async def ensure_bot_running():
    hb = await get_process_heartbeat(BOT_PROCESS_NAME)
    if hb is None:
        start_bot()
        return

    pid, created_at, updated_at = hb

    now = datetime.now(timezone.utc)

    if now - updated_at < timedelta(seconds=45):
        return

    print("Bot heartbeat expired, bot will restart")

    await terminate_process(
        pid,
        created_at,
    )

    await delete_process_heartbeat(BOT_PROCESS_NAME)

    start_bot()


if __name__ == "__main__":
    async_run(main)
