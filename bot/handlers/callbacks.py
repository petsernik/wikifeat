import asyncio

from telegram import Update, InputMediaAnimation, InputMediaPhoto
from telegram.ext import ContextTypes

from bot.handlers.registry import callback
from bot.handlers.workers import processing_message_worker
from bot.keyboards.common import get_more_random_keyboard, get_retry_keyboard
from bot.keyboards.disambig import build_disambig_nav_keyboard
from bot.services.article import handle_article
from bot.services.disambig import get_session, get_disambig_keyboard_from_session
from bot.services.render import notify
from db import get_lang, set_lang, get_random_featured_title
from i18n import translate, TKey
from models import DisambigSession
from utils import normalize_lang


async def get_user_lang(user_id: int, tg_lang: str | None):
    lang = await get_lang(user_id)
    if lang:
        return lang
    return await set_user_lang(user_id, tg_lang)


async def update_message(query, session: DisambigSession):
    level = session.current()
    if not level:
        return
    keyboard = get_disambig_keyboard_from_session(session)
    msg = query.message
    if level.media:
        if level.media_is_animation:
            media_obj = InputMediaAnimation(
                media=level.media,
                caption=level.caption,
                parse_mode="HTML",
            )
        else:
            media_obj = InputMediaPhoto(
                media=level.media,
                caption=level.caption,
                parse_mode="HTML",
            )
        await msg.edit_media(media=media_obj, reply_markup=keyboard)
    elif msg.photo or msg.animation or msg.video:
        await msg.edit_caption(
            caption=level.caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await msg.edit_text(
            text=level.caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


async def set_user_lang(user_id: int, lang: str) -> str:
    lang = normalize_lang(lang)
    await set_lang(user_id, lang)
    return lang


@callback("^lang:")
async def lang_select(update: Update, _: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id

    lang_code = query.data.split(":", 1)[1]

    await set_user_lang(uid, lang_code)

    await query.answer()

    await query.edit_message_text(
        translate(
            normalize_lang(lang_code),
            TKey.LANG_CHANGED,
            value=lang_code
        )
    )


@callback("^more_random$")
async def more_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id

    lang_val = await get_user_lang(uid, query.from_user.language_code)

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
            query.message.chat.id,
            check_limit=True,
            keyboard=get_more_random_keyboard(),
        )
        finished_ok.set()
    except Exception:
        finished_bad.set()
    finally:
        await processing_message_task


@callback("^try_again\\|")
async def try_again_this_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    _, request_type, title = query.data.split("|", 2)

    uid = query.from_user.id
    lang_val = await get_user_lang(uid, query.from_user.language_code)

    if request_type == "random":
        keyboard = get_more_random_keyboard()
    else:
        keyboard = None

    try:
        await handle_article(
            update,
            context,
            title,
            lang_val,
            uid,
            query.message.chat.id,
            check_limit=True,
            keyboard=keyboard,
        )
        await update.effective_message.delete()
    except Exception:
        await notify(update, translate(lang_val, TKey.PROCESSING_ERROR))


@callback("^page\\|")
async def disambig_page(update, context):
    query = update.callback_query

    mid = query.message.message_id
    session = get_session(context, mid)

    direction = query.data.split("|")[1]  # "prev" or "next"

    if not session.shift_page(direction):
        uid = query.from_user.id
        lang_val = await get_user_lang(uid, query.from_user.language_code)
        await notify(update, translate(lang_val, TKey.DISAMBIG_END))
        return

    await update_message(query, session)


@callback("^open\\|")
async def disambig_open(update, context):
    query = update.callback_query

    await query.answer()

    mid = query.message.message_id
    session = get_session(context, mid)

    level = session.current()
    if not level:
        return

    idx = int(query.data.split("|")[1])

    if not (0 <= idx < len(level.titles)):
        return

    session.set_index(idx)

    uid = query.from_user.id
    lang_val = await get_user_lang(uid, query.from_user.language_code)

    await handle_article(
        update,
        context,
        level.titles[idx],
        lang_val,
        uid,
        query.message.chat.id,
        check_limit=True,
        use_cache=True,
        edit_message=query.message,
        page=session.page,
        keyboard=build_disambig_nav_keyboard(),
    )


@callback("^nav\\|")
async def disambig_nav(update, context):
    query = update.callback_query

    mid = query.message.message_id
    session = get_session(context, mid)

    direction = query.data.split("|")[1]  # "prev" or "next"

    ok = session.shift(direction)

    if not ok:
        # Граница уровня — возвращаемся к списку родителя
        if not session.back():
            uid = query.from_user.id
            lang_val = await get_user_lang(uid, query.from_user.language_code)
            await notify(update, translate(lang_val, TKey.DISAMBIG_END))
            return
        await update_message(query, session)
        return

    level = session.current()
    if not level:
        await query.answer()
        return

    idx = session.index

    uid = query.from_user.id
    lang_val = await get_user_lang(uid, query.from_user.language_code)

    await handle_article(
        update,
        context,
        level.titles[idx],
        lang_val,
        uid,
        query.message.chat.id,
        check_limit=True,
        use_cache=True,
        edit_message=query.message,
        page=session.page,
        keyboard=build_disambig_nav_keyboard(),
    )


@callback("^back$")
async def disambig_back(update, context, from_nav=False):
    query = update.callback_query

    await query.answer()

    mid = query.message.message_id
    session = get_session(context, mid)

    if not from_nav and not session.back():
        return

    level = session.current()

    keyboard = get_disambig_keyboard_from_session(session)

    msg = query.message

    if level.media:
        if level.media_is_animation:
            media_obj = InputMediaAnimation(
                media=level.media,
                caption=level.caption,
                parse_mode="HTML",
            )
        else:
            media_obj = InputMediaPhoto(
                media=level.media,
                caption=level.caption,
                parse_mode="HTML",
            )

        await msg.edit_media(media=media_obj, reply_markup=keyboard)
        return

    if msg.photo or msg.animation or msg.video:
        await msg.edit_caption(
            caption=level.caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await msg.edit_text(
            text=level.caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


@callback("^back_nav$")
async def disambig_back_nav_callback(update, context):
    await disambig_back(update, context, from_nav=True)


@callback("^noop$")
async def noop(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


@callback("^delete$")
async def delete(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.delete()
