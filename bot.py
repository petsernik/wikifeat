import time
from typing import Dict

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, InputMediaAnimation, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import (
    TELEGRAM_BOT_TOKEN, Config, DAILY_TOTAL_LIMIT, DAILY_USER_LIMIT, SPAM_INTERVAL,
    CMD_STATUS, CMD_RANDOM, CMD_LIMIT, CMD_LANG, CMD_ABOUT,
    CMD_GET, CMD_CANCEL, OWNER_ID, CHANNEL_USERNAME, CMD_UPDATE, SELF_MADE_IMAGE_CASE
)
from core import get_article, get_caption, get_ctx_req_by_config
from db import get_pool, init_db, close_db, get_random_featured_title, get_lang, set_lang, get_user_limit, \
    reset_user_limit, has_featured_articles, update_featured_articles_in_db, update_image_desc
from i18n import TKey, TRANSLATIONS, translate
from models import DisambigSession, DisambigLevel
from parsers import fetch_featured_titles
from script import main as script_main
from utils import normalize_lang, get_img_buf_by_text

# =========================
# FSM STATE
# =========================
STATE_NONE = "none"
STATE_GET = "get"
STATE_UPDATE = "update"

user_state: Dict[int, str] = {}


def get_state(user_id: int):
    return user_state.get(user_id, STATE_NONE)


def set_state(user_id: int, state: str):
    user_state[user_id] = state


def clear_state(user_id: int):
    user_state[user_id] = STATE_NONE


# =========================
# LIMIT / SPAM
# =========================
user_last_request_time = {}


def is_spam(user_id: int) -> bool:
    now = time.time()
    last = user_last_request_time.get(user_id, 0)

    if now - last < SPAM_INTERVAL:
        return True

    user_last_request_time[user_id] = now
    return False


async def check_and_increment_limit(user_id: int) -> bool:
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():

            # --- global limit ---
            total_row = await conn.fetchrow(
                "SELECT total FROM global_limits WHERE date = CURRENT_DATE"
            )
            total = total_row["total"] if total_row else 0

            if total >= DAILY_TOTAL_LIMIT:
                return False

            # --- user limit ---
            user_row = await conn.fetchrow(
                """
                SELECT count FROM user_limits
                WHERE user_id=$1 AND date=CURRENT_DATE
                """,
                user_id
            )
            user_count = user_row["count"] if user_row else 0

            if user_count >= DAILY_USER_LIMIT:
                return False

            # --- increment user ---
            await conn.execute(
                """
                INSERT INTO user_limits(user_id, date, count)
                VALUES($1, CURRENT_DATE, 1)
                ON CONFLICT (user_id, date)
                DO UPDATE SET count = user_limits.count + 1
                """,
                user_id
            )

            # --- increment global ---
            await conn.execute(
                """
                INSERT INTO global_limits(date, total)
                VALUES(CURRENT_DATE, 1)
                ON CONFLICT (date)
                DO UPDATE SET total = global_limits.total + 1
                """
            )

            return True


async def is_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    m = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
    return m.status in ("member", "administrator", "creator")


async def get_user_lang(user_id: int, tg_lang: str | None):
    lang = await get_lang(user_id)
    if lang:
        return lang
    return await set_user_lang(user_id, tg_lang)


async def set_user_lang(user_id: int, lang: str) -> str:
    lang = normalize_lang(lang)
    await set_lang(user_id, lang)
    return lang


# =========================
# ACCESS CONTROL
# =========================
async def check_access(context, user_id: int, decrease=False):
    if is_spam(user_id):
        return False, TKey.SPAM_BLOCK

    if not await is_subscribed(context, user_id):
        return False, TKey.NEED_SUBSCRIPTION

    if decrease:
        if not await check_and_increment_limit(user_id):
            return False, TKey.LIMIT_EXCEEDED

    return True, TKey.STATUS_OK


# =========================
# ARTICLE SENDER
# =========================
def get_more_keyboard():
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄", callback_data="more_random")]
    ])
    return kb


async def _get_config(chat_id, query, lang) -> Config:
    return Config(
        TELEGRAM_CHANNELS=[chat_id],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=query,
        LANG_CODE=lang,
        USE_AND_UPDATE_LAST_FEATURED_TITLE=False,
        WITH_IMAGE=True,
    )


async def edit(update, context, article, caption, keyboard, media=None, media_is_animation=False):
    msg = update.callback_query.message

    # =========================
    # MEDIA LOGIC (КАК В send)
    # =========================
    if media:
        if media_is_animation:
            media_obj = InputMediaAnimation(
                media=media,
                caption=caption,
                parse_mode="HTML"
            )
        else:
            media_obj = InputMediaPhoto(
                media=media,
                caption=caption,
                parse_mode="HTML"
            )

        await msg.edit_media(
            media=media_obj,
            reply_markup=keyboard
        )
    else:
        await msg.edit_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )


PAGE_SIZE = 8


def get_session(context, message_id: int):
    return context.user_data.setdefault("disambig_sessions", {}).setdefault(
        message_id,
        DisambigSession(message_id=message_id)
    )


def clamp_page(page: int, total: int) -> int:
    max_page = max(0, (total - 1) // PAGE_SIZE)
    return max(0, min(page, max_page))


def build_disambig_nav_keyboard(idx: int, total: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"nav|{idx - 1}" if idx > 0 else "noop"
            ),
            InlineKeyboardButton("↩️", callback_data="back_nav"),
            InlineKeyboardButton(
                "➡️",
                callback_data=f"nav|{idx + 1}" if idx < total - 1 else "noop"
            )
        ]
    ])


def build_disambig_keyboard(links: list[str], page: int = 0):
    start = page * PAGE_SIZE
    chunk = links[start:start + PAGE_SIZE]

    keyboard = [
        [InlineKeyboardButton(text=link, callback_data=f"open|{start + i}")]
        for i, link in enumerate(chunk)
    ]

    nav = [
        InlineKeyboardButton(
            "⬅️",
            callback_data=f"page|{page - 1}" if page > 0 else "noop"
        ),
        InlineKeyboardButton("↩️", callback_data="back"),
        InlineKeyboardButton(
            "➡️",
            callback_data=f"page|{page + 1}"
        )
    ]
    keyboard.append(nav)

    return InlineKeyboardMarkup(keyboard)


async def render_article(
        context,
        chat_id,
        lang,
        query,
        *,
        keyboard=None,
        ctx_req=None,
        page=0,
        edit_message=None,
):
    cfg = await _get_config(chat_id, query, lang)

    article, ctx = await get_article(cfg, ctx_req)

    if not article:
        if edit_message:
            if edit_message.photo or edit_message.animation or edit_message.video:
                await edit_message.edit_caption("Error")
            else:
                await edit_message.edit_text("Error")
        else:
            await context.bot.send_message(chat_id, "Error")
        return

    # =========================
    # MEDIA
    # =========================
    media, media_is_animation = None, False

    if article.image:
        if article.image.desc == SELF_MADE_IMAGE_CASE:
            media = get_img_buf_by_text(article.title)
        else:
            media = article.image.desc
            media_is_animation = article.image.is_animation

    # =========================
    # CAPTION
    # =========================
    if article.is_disambig:
        caption = get_caption(
            article,
            cfg.RULES_URL,
            ctx,
            use_only_first_paragraph=True
        )
    else:
        caption = get_caption(article, cfg.RULES_URL, ctx)

    file_id = None

    # =========================
    # DISAMBIG SESSION UPDATE
    # =========================

    if article.is_disambig:
        if edit_message:
            session = get_session(context, edit_message.message_id)

            session.push(
                DisambigLevel(
                    titles=article.disambig_titles,
                    caption=caption,
                    media=media,
                    media_is_animation=media_is_animation,
                )
            )

            keyboard = get_disambig_keyboard_from_session(session)

        if not edit_message:
            keyboard = build_disambig_keyboard(
                article.disambig_titles,
                0
            )
    else:
        keyboard = keyboard
    # =========================
    # EDIT EXISTING MESSAGE
    # =========================
    if edit_message:

        if media:

            if media_is_animation:
                media_obj = InputMediaAnimation(
                    media=media,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                media_obj = InputMediaPhoto(
                    media=media,
                    caption=caption,
                    parse_mode="HTML"
                )

            result = await edit_message.edit_media(
                media=media_obj,
                reply_markup=keyboard
            )

            if isinstance(result, type(edit_message)):

                if result.animation:
                    file_id = result.animation.file_id
                elif result.photo:
                    file_id = result.photo[-1].file_id

            if not file_id:
                file_id = media

        else:

            if edit_message.photo or edit_message.animation or edit_message.video:
                await edit_message.edit_caption(
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                await edit_message.edit_text(
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

        msg = edit_message

    # =========================
    # SEND NEW MESSAGE
    # =========================
    else:

        if media:

            if media_is_animation:

                msg = await context.bot.send_animation(
                    chat_id,
                    animation=media,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

                file_id = msg.animation.file_id

            else:

                msg = await context.bot.send_photo(
                    chat_id,
                    photo=media,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

                file_id = msg.photo[-1].file_id

        else:
            msg = await context.bot.send_message(
                chat_id,
                caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )

    # =========================
    # CACHE UPDATE
    # =========================
    if media and article.image and article.image.desc != file_id:
        article.image.desc = file_id
        if article.is_disambig and edit_message:
            session = get_session(context, msg.message_id)
            session.current().media = file_id
        await update_image_desc(article.link, file_id)

    # =========================
    # DISAMBIG STATE
    # =========================
    if article.is_disambig and not edit_message:
        session = get_session(context, msg.message_id)

        session.push(
            DisambigLevel(
                titles=article.disambig_titles,
                caption=caption,
                media=file_id,
                media_is_animation=media_is_animation,
            )
        )


async def notify(update, text):
    if update.callback_query:
        await update.callback_query.answer(
            text=text or "",
            show_alert=bool(text)
        )
    elif text:
        await update.effective_message.reply_text(text)


async def handle_article(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        title: str,
        lang_val: str,
        uid: int,
        chat_id: int,
        check_limit: bool = True,
        keyboard=None,
        use_cache=True,
        edit_message=None,
        page=0,
):
    notify_text = None

    try:
        if not title:
            notify_text = "bot error: empty title when handling article"
            return

        ok, reason = await check_access(context, update.effective_user.id)
        if not ok:
            notify_text = translate(lang_val, reason)
            return

        ctx_req = await get_ctx_req_by_config(
            await _get_config(chat_id, title, lang_val),
            use_cache
        )

        # кеш → сразу отправляем без лимита
        if ctx_req.cached:
            await render_article(
                context,
                chat_id,
                lang_val,
                title,
                keyboard=keyboard,
                ctx_req=ctx_req,
                edit_message=edit_message,
                page=page,
            )
            return

        # лимит
        if check_limit:
            ok = await check_and_increment_limit(uid)

            if not ok:
                notify_text = translate(lang_val, TKey.LIMIT_EXCEEDED)
                return

        await render_article(
            context,
            chat_id,
            lang_val,
            title,
            keyboard=keyboard,
            ctx_req=ctx_req,
            edit_message=edit_message,
            page=page,
        )

    finally:
        await notify(update, notify_text)


def get_disambig_keyboard_from_session(session: DisambigSession):
    level = session.current()
    if not level:
        return None

    return build_disambig_keyboard(level.titles, session.page)


# =========================
# COMMANDS
# =========================
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


async def about(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tg_lang = update.effective_user.language_code

    lang = await get_user_lang(user_id, tg_lang)

    await update.message.reply_text(
        translate(lang, TKey.ABOUT)
    )


async def status(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tg_lang = update.effective_user.language_code

    lang = await get_user_lang(user_id, tg_lang)

    await update.message.reply_text(
        translate(lang, TKey.STATUS_OK)
    )


async def limit(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    used = await get_user_limit(user_id)
    lang = await get_user_lang(user_id, update.effective_user.language_code)

    await update.message.reply_text(
        translate(lang, TKey.LIMIT_REMAINING, count=DAILY_USER_LIMIT - used)
    )


# =========================
# LANG
# =========================
def get_lang_keyboard():
    buttons = [
        InlineKeyboardButton(lang, callback_data=f"lang:{lang}")
        for lang in sorted(TRANSLATIONS.keys())
    ]

    rows = [buttons[i:i + 4] for i in range(0, len(buttons), 4)]
    return InlineKeyboardMarkup(rows)


async def cmd_lang(update: Update, _: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang_code = update.effective_user.language_code

    lang_val = await get_user_lang(uid, lang_code)

    await update.message.reply_text(
        translate(lang_val, TKey.AVAILABLE_LANGS, values=", ".join(sorted(TRANSLATIONS.keys()))),
        reply_markup=get_lang_keyboard()
    )


# =========================
# RANDOM
# =========================
async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang_val = await get_user_lang(uid, update.effective_user.language_code)

    title = await get_random_featured_title(lang_val)

    await handle_article(
        update,
        context,
        title,
        lang_val,
        uid,
        update.effective_chat.id,
        check_limit=True,
        keyboard=get_more_keyboard(),
    )


# =========================
# GET FLOW (FSM)
# =========================
async def get_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang_val = await get_user_lang(uid, update.effective_user.language_code)

    used = await get_user_limit(uid)

    if used >= DAILY_USER_LIMIT:
        await update.message.reply_text(translate(lang_val, TKey.LIMIT_EXCEEDED))
        return

    set_state(uid, STATE_GET)

    await update.message.reply_text(translate(lang_val, TKey.GET_PROMPT))


async def update_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang_val = await get_user_lang(uid, update.effective_user.language_code)

    used = await get_user_limit(uid)

    if used >= DAILY_USER_LIMIT:
        await update.message.reply_text(translate(lang_val, TKey.LIMIT_EXCEEDED))
        return

    set_state(uid, STATE_UPDATE)

    await update.message.reply_text(translate(lang_val, TKey.GET_PROMPT))


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()

    state = get_state(uid)

    lang_val = await get_user_lang(uid, update.effective_user.language_code)

    if state in (STATE_GET, STATE_NONE, STATE_UPDATE):
        try:
            await handle_article(
                update,
                context,
                text,
                lang_val,
                uid,
                update.effective_chat.id,
                check_limit=True,
                use_cache=state != STATE_UPDATE,
            )
        except:
            await update.message.reply_text(translate(lang_val, TKey.GET_ERROR))
        finally:
            clear_state(uid)


# =========================
# CANCEL
# =========================
async def cancel(update: Update, _: ContextTypes.DEFAULT_TYPE):
    clear_state(update.effective_user.id)

    uid = update.effective_user.id
    lang_val = await get_user_lang(uid, update.effective_user.language_code)

    await update.message.reply_text(translate(lang_val, TKey.CANCEL_OK))


# =========================
# CALLBACKS
# =========================
async def lang_select(update: Update, _: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id

    lang_code = query.data.split(":", 1)[1]

    await set_user_lang(uid, lang_code)

    await query.answer()

    await query.edit_message_text(
        translate(normalize_lang(lang_code), TKey.LANG_CHANGED, value=lang_code)
    )


async def more_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id

    lang_val = await get_user_lang(uid, query.from_user.language_code)

    title = await get_random_featured_title(lang_val)

    await handle_article(
        update,
        context,
        title,
        lang_val,
        uid,
        query.message.chat.id,
        check_limit=True,
        keyboard=get_more_keyboard(),
    )


async def disambig_page(update, context):
    query = update.callback_query
    await query.answer()

    mid = query.message.message_id
    session = get_session(context, mid)

    level = session.current()
    if not level:
        return

    page = int(query.data.split("|")[1])
    page = clamp_page(page, len(level.titles))

    session.page = page

    keyboard = get_disambig_keyboard_from_session(session)

    await query.message.edit_reply_markup(reply_markup=keyboard)


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

    session.set_index(idx, PAGE_SIZE)

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
        keyboard=build_disambig_nav_keyboard(idx, len(level.titles))
    )


async def disambig_nav(update, context):
    query = update.callback_query
    await query.answer()

    mid = query.message.message_id
    session = get_session(context, mid)

    level = session.current()
    if not level:
        return

    idx = int(query.data.split("|")[1])
    idx = max(0, min(idx, len(level.titles) - 1))

    session.set_index(idx, PAGE_SIZE)

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
        keyboard=build_disambig_nav_keyboard(idx, len(level.titles))
    )


async def disambig_back_nav(update, context):
    await disambig_back(update, context, from_nav=True)


async def disambig_back(update, context, from_nav=False):
    query = update.callback_query
    await query.answer()

    mid = query.message.message_id
    session = get_session(context, mid)

    if not from_nav and not session.back():
        return
    level = session.current()

    page = session.page

    keyboard = get_disambig_keyboard_from_session(session)

    caption = level.caption
    media = level.media
    media_is_animation = level.media_is_animation

    msg = query.message

    if media:

        if media_is_animation:
            media_obj = InputMediaAnimation(
                media=media,
                caption=caption,
                parse_mode="HTML"
            )
        else:
            media_obj = InputMediaPhoto(
                media=media,
                caption=caption,
                parse_mode="HTML"
            )

        await msg.edit_media(
            media=media_obj,
            reply_markup=keyboard
        )
        return

    if msg.photo or msg.animation or msg.video:
        await msg.edit_caption(
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await msg.edit_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )


async def noop(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


# =========================
# OWNER COMMANDS
# =========================
async def reborn(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await reset_user_limit(OWNER_ID)

    await update.message.reply_text("Reborn OK")


async def release(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text("Running release tasks...")

    try:
        await script_main(context.application)
        await update.message.reply_text("Release finished OK")
    except Exception as e:
        await update.message.reply_text(f"Release failed: {e}")


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

    # =========================
    # commands
    # =========================
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(CMD_ABOUT, about))
    app.add_handler(CommandHandler(CMD_STATUS, status))
    app.add_handler(CommandHandler(CMD_LIMIT, limit))
    app.add_handler(CommandHandler(CMD_LANG, cmd_lang))
    app.add_handler(CommandHandler(CMD_RANDOM, random))
    app.add_handler(CommandHandler(CMD_GET, get_cmd))
    app.add_handler(CommandHandler(CMD_CANCEL, cancel))
    app.add_handler(CommandHandler(CMD_UPDATE, update_cmd))
    app.add_handler(CommandHandler("reborn", reborn))
    app.add_handler(CommandHandler("release", release))

    # callbacks
    app.add_handler(CallbackQueryHandler(lang_select, pattern="^lang:"))
    app.add_handler(CallbackQueryHandler(more_random, pattern="^more_random$"))
    app.add_handler(CallbackQueryHandler(disambig_page, pattern="^page\\|"))
    app.add_handler(CallbackQueryHandler(disambig_open, pattern="^open\\|"))
    app.add_handler(CallbackQueryHandler(disambig_nav, pattern="^nav\\|"))
    app.add_handler(CallbackQueryHandler(disambig_back, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(disambig_back_nav, pattern="^back_nav$"))
    app.add_handler(CallbackQueryHandler(noop, pattern="^noop$"))

    # text router
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # =========================
    # RUN
    # =========================
    app.run_polling()


# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    main()
