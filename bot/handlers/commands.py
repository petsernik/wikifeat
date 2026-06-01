import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.callbacks import get_user_lang
from bot.handlers.registry import command
from bot.handlers.workers import processing_message_worker
from bot.keyboards.common import get_more_random_keyboard, get_retry_keyboard
from bot.keyboards.lang import get_lang_keyboard
from bot.services.article import handle_article
from bot.state.user_state import (
    STATE_GET,
    STATE_UPDATE,
    set_state,
    clear_state,
)
from constants import (
    DAILY_USER_LIMIT,
    CMD_ABOUT,
    CMD_STATUS,
    CMD_LIMIT,
    CMD_LANG,
    CMD_RANDOM,
    CMD_GET,
    CMD_CANCEL,
    CMD_UPDATE,
)
from db import (
    get_lang,
    set_lang,
    get_user_limit,
    get_random_featured_title,
)
from i18n import translate, TKey, TRANSLATIONS
from utils import normalize_lang


@command("start")
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tg_lang = update.effective_user.language_code

    lang = await get_lang(user_id)

    if not lang:
        lang = normalize_lang(tg_lang)
        await set_lang(user_id, lang)

    await update.message.reply_text(
        translate(lang, TKey.ABOUT)
    )


@command(CMD_ABOUT)
async def about(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tg_lang = update.effective_user.language_code

    lang = await get_user_lang(user_id, tg_lang)

    await update.message.reply_text(
        translate(lang, TKey.ABOUT)
    )


@command(CMD_STATUS)
async def status(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tg_lang = update.effective_user.language_code

    lang = await get_user_lang(user_id, tg_lang)

    await update.message.reply_text(
        translate(lang, TKey.STATUS_OK)
    )


@command(CMD_LIMIT)
async def limit(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    used = await get_user_limit(user_id)
    lang = await get_user_lang(user_id, update.effective_user.language_code)

    await update.message.reply_text(
        translate(
            lang,
            TKey.LIMIT_REMAINING,
            count=DAILY_USER_LIMIT - used
        )
    )


@command(CMD_LANG)
async def cmd_lang(update: Update, _: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang_code = update.effective_user.language_code

    lang_val = await get_user_lang(uid, lang_code)

    await update.message.reply_text(
        translate(
            lang_val,
            TKey.AVAILABLE_LANGS,
            values=", ".join(sorted(TRANSLATIONS.keys()))
        ),
        reply_markup=get_lang_keyboard()
    )


@command(CMD_RANDOM)
async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang_val = await get_user_lang(uid, update.effective_user.language_code)
    title = await get_random_featured_title(lang_val)

    finished_ok = asyncio.Event()
    finished_bad = asyncio.Event()
    processing_message_task = asyncio.create_task(
        processing_message_worker(
            update,
            lang_val,
            title,
            finished_ok,
            finished_bad,
            keyboard=get_retry_keyboard(lang_val, title, "random"),
        )
    )

    try:
        await handle_article(
            update,
            context,
            title,
            lang_val,
            uid,
            update.effective_chat.id,
            check_limit=True,
            keyboard=get_more_random_keyboard(),
        )
        finished_ok.set()
    except Exception:
        finished_bad.set()
    finally:
        await processing_message_task


# =========================
# GET FLOW (FSM)
# =========================
@command(CMD_GET)
async def get_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang_val = await get_user_lang(uid, update.effective_user.language_code)

    used = await get_user_limit(uid)

    if used >= DAILY_USER_LIMIT:
        await update.message.reply_text(
            translate(lang_val, TKey.LIMIT_EXCEEDED)
        )
        return

    set_state(uid, STATE_GET)

    await update.message.reply_text(
        translate(lang_val, TKey.GET_PROMPT)
    )


@command(CMD_UPDATE)
async def update_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang_val = await get_user_lang(uid, update.effective_user.language_code)

    used = await get_user_limit(uid)

    if used >= DAILY_USER_LIMIT:
        await update.message.reply_text(
            translate(lang_val, TKey.LIMIT_EXCEEDED)
        )
        return

    set_state(uid, STATE_UPDATE)

    await update.message.reply_text(
        translate(lang_val, TKey.GET_PROMPT)
    )


@command(CMD_CANCEL)
async def cancel(update: Update, _: ContextTypes.DEFAULT_TYPE):
    clear_state(update.effective_user.id)

    uid = update.effective_user.id
    lang_val = await get_user_lang(uid, update.effective_user.language_code)

    await update.message.reply_text(
        translate(lang_val, TKey.CANCEL_OK)
    )
