import time
from typing import Dict

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
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


def build_disambig_nav_keyboard(idx: int, total: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️", callback_data=f"nav|{idx - 1}"),
            InlineKeyboardButton("↩️", callback_data="back"),
            InlineKeyboardButton("➡️", callback_data=f"nav|{idx + 1}")
        ]
    ])


def build_disambig_keyboard(links: list[str], page: int = 0):
    start = page * PAGE_SIZE
    chunk = links[start:start + PAGE_SIZE]

    keyboard = [
        [InlineKeyboardButton(text=link, callback_data=f"open|{start + i}")]
        for i, link in enumerate(chunk)
    ]

    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton("⬅️", callback_data=f"page|{page - 1}")
        )

    if start + PAGE_SIZE < len(links):
        nav.append(
            InlineKeyboardButton("➡️", callback_data=f"page|{page + 1}")
        )

    if nav:
        keyboard.append(nav)

    return InlineKeyboardMarkup(keyboard)


async def send(context, chat_id, lang, query, *, keyboard=None, ctx_req=None, page=0):
    cfg = await _get_config(chat_id, query, lang)
    article, ctx = await get_article(cfg, ctx_req)

    if not article:
        await context.bot.send_message(chat_id, "Error")
        return

    # =========================
    # COMMON MEDIA LOGIC
    # =========================
    media, media_is_animation = None, False
    if article.image:
        if article.image.desc == SELF_MADE_IMAGE_CASE:
            media = get_img_buf_by_text(article.title)
            media_is_animation = False
        else:
            media = article.image.desc
            media_is_animation = article.image.is_animation

    # =========================
    # DISAMBIG / NORMAL LOGIC
    # =========================
    if article.is_disambig:
        caption = get_caption(
            article,
            cfg.RULES_URL,
            ctx,
            use_only_first_paragraph=True
        )
        context.user_data["disambig_titles"] = article.disambig_titles
        context.user_data["disambig_root"] = {
            "links": article.disambig_titles,
            "page": page,
            "caption": caption,
            "media": media,
            "media_is_animation": media_is_animation,
        }
        keyboard = build_disambig_keyboard(article.disambig_titles, page)
    else:
        caption = get_caption(article, cfg.RULES_URL, ctx)
        keyboard = keyboard

    # =========================
    # SEND MEDIA
    # =========================
    # msg = None
    file_id = None

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
        await context.bot.send_message(
            chat_id,
            caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # =========================
    # CACHE UPDATE
    # =========================
    if media and article.image.desc != file_id:
        article.image.desc = file_id
        await update_image_desc(article.link, file_id)
        if article.is_disambig:
            context.user_data["disambig_root"]["media"] = file_id


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
            await send(
                context,
                chat_id,
                lang_val,
                title,
                keyboard=keyboard,
                ctx_req=ctx_req
            )
            return

        # лимит
        if check_limit:
            ok = await check_and_increment_limit(uid)

            if not ok:
                notify_text = translate(lang_val, TKey.LIMIT_EXCEEDED)
                return

        await send(
            context,
            chat_id,
            lang_val,
            title,
            keyboard=keyboard,
            ctx_req=ctx_req
        )

    finally:
        await notify(update, notify_text)


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

    page = int(query.data.split("|")[1])

    links = context.user_data.get("disambig_titles", [])

    kb = build_disambig_keyboard(links, page)

    await query.message.edit_reply_markup(reply_markup=kb)


async def disambig_open(update, context):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.split("|")[1])
    links = context.user_data.get("disambig_titles", [])

    if not (0 <= idx < len(links)):
        return

    context.user_data["disambig_index"] = idx
    page = idx // PAGE_SIZE
    context.user_data["disambig_page"] = page
    context.user_data["disambig_titles"] = links

    uid = query.from_user.id
    lang_val = await get_user_lang(uid, query.from_user.language_code)

    title = links[idx]

    cfg = await _get_config(query.message.chat.id, title, lang_val)
    article, ctx = await get_article(cfg, await get_ctx_req_by_config(cfg, True))

    # =========================
    # MEDIA (1:1 как send)
    # =========================
    media, media_is_animation = None, False

    if article.image:
        if article.image.desc == SELF_MADE_IMAGE_CASE:
            media = get_img_buf_by_text(article.title)
            media_is_animation = False
        else:
            media = article.image.desc
            media_is_animation = article.image.is_animation

    # =========================
    # CAPTION (1:1 как send)
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

    # =========================
    # KEYBOARD (как send)
    # =========================
    keyboard = build_disambig_nav_keyboard(idx, len(links))

    # =========================
    # EDIT INSTEAD OF SEND
    # =========================
    await edit(
        update,
        context,
        article,
        caption,
        keyboard,
        media,
        media_is_animation
    )


async def disambig_nav(update, context):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.split("|")[1])
    links = context.user_data.get("disambig_titles", [])

    idx = max(0, min(idx, len(links) - 1))
    context.user_data["disambig_index"] = idx

    page = idx // PAGE_SIZE
    context.user_data["disambig_page"] = page

    uid = query.from_user.id
    lang_val = await get_user_lang(uid, query.from_user.language_code)

    title = links[idx]

    cfg = await _get_config(query.message.chat.id, title, lang_val)
    article, ctx = await get_article(cfg, await get_ctx_req_by_config(cfg, True))

    # === media ====
    media, media_is_animation = None, False

    if article.image:
        if article.image.desc == SELF_MADE_IMAGE_CASE:
            media = get_img_buf_by_text(article.title)
        else:
            media = article.image.desc
            media_is_animation = article.image.is_animation

    # === caption ====
    caption = get_caption(article, cfg.RULES_URL, ctx)

    keyboard = build_disambig_nav_keyboard(idx, len(links))

    await edit(
        update,
        context,
        article,
        caption,
        keyboard,
        media,
        media_is_animation
    )


from telegram import InputMediaPhoto, InputMediaAnimation


async def disambig_back(update, context):
    query = update.callback_query
    await query.answer()

    root = context.user_data.get("disambig_root", {})
    links = root.get("links", [])
    page = context.user_data.get("disambig_page", 0)

    context.user_data.pop("disambig_index", None)

    if not links:
        await query.message.edit_text("No data")
        return

    keyboard = build_disambig_keyboard(links, page)

    msg = query.message

    caption = root.get("caption", "Choose option:")

    # =========================
    # CASE 1: MESSAGE WITH MEDIA
    # =========================
    if msg.photo or msg.animation or msg.video:

        # ВАЖНО: нужно вернуть СТАРУЮ картинку
        media = root.get("media")
        media_is_animation = root.get("media_is_animation", False)

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
            # fallback если медиа нет
            await msg.edit_caption(
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        return

    # =========================
    # CASE 2: TEXT MESSAGE
    # =========================
    await msg.edit_text(
        text=caption,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


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
