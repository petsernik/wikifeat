import json
import os
import threading
import time
from datetime import datetime, UTC

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import (
    TELEGRAM_BOT_TOKEN, Config, TMP_FOLDER_PATH, LIMIT_FILE,
    DAILY_TOTAL_LIMIT, DAILY_USER_LIMIT, SPAM_INTERVAL,
    CMD_STATUS, CMD_RANDOM, CMD_LIMIT, CMD_LANG, CMD_ABOUT,
    CMD_GET, CMD_CANCEL, OWNER_ID
)

from core import get_article, get_caption
from i18n import TKey, TRANSLATIONS, translate

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# =========================
# FSM STATE
# =========================
STATE_NONE = "none"
STATE_GET = "get"

user_state = {}


def get_state(user_id: int):
    return user_state.get(user_id, STATE_NONE)


def set_state(user_id: int, state: str):
    user_state[user_id] = state


def clear_state(user_id: int):
    user_state[user_id] = STATE_NONE


# =========================
# LIMIT / SPAM
# =========================
limit_lock = threading.Lock()
user_last_request_time = {}

CHANNEL_USERNAME = "@wikifeat"

LANG_FILE = os.path.join(TMP_FOLDER_PATH, "user_lang.json")
lang_lock = threading.Lock()

SUPPORTED_LANGS = TRANSLATIONS.keys()


def is_spam(user_id: int) -> bool:
    now = time.time()
    last = user_last_request_time.get(user_id, 0)

    if now - last < SPAM_INTERVAL:
        return True

    user_last_request_time[user_id] = now
    return False


def load_limit():
    if not os.path.exists(LIMIT_FILE):
        return {"date": None, "total": 0, "users": {}}

    try:
        with open(LIMIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"date": None, "total": 0, "users": {}}


def save_limit(data):
    tmp = LIMIT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, LIMIT_FILE)


def get_today():
    return datetime.now(UTC).strftime("%Y-%m-%d")


def check_and_increment_limit(user_id: int) -> bool:
    with limit_lock:
        today = get_today()
        data = load_limit()

        if data["date"] != today:
            data = {"date": today, "total": 0, "users": {}}

        if data["total"] >= DAILY_TOTAL_LIMIT:
            return False

        uid = str(user_id)
        count = data["users"].get(uid, 0)

        if count >= DAILY_USER_LIMIT:
            return False

        data["total"] += 1
        data["users"][uid] = count + 1

        save_limit(data)
        return True


def is_subscribed(user_id: int) -> bool:
    m = bot.get_chat_member(CHANNEL_USERNAME, user_id)
    return m.status in ("member", "administrator", "creator")


# =========================
# LANG SYSTEM
# =========================
def normalize_lang(code: str | None):
    if not code:
        return "en"
    base = code.lower().split("-")[0]
    return base if base in SUPPORTED_LANGS else "en"


def load_langs():
    if not os.path.exists(LANG_FILE):
        return {}
    try:
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_langs(data):
    tmp = LANG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, LANG_FILE)


def get_user_lang(user_id: int, tg_lang: str | None):
    data = load_langs()
    if str(user_id) in data:
        return data[str(user_id)]
    return normalize_lang(tg_lang)


def set_user_lang(user_id: int, lang: str):
    lang = normalize_lang(lang)
    with lang_lock:
        data = load_langs()
        data[str(user_id)] = lang
        save_langs(data)


# =========================
# ACCESS CONTROL
# =========================
def check_access(user_id: int, decrease=False):
    if is_spam(user_id):
        return False, TKey.SPAM_BLOCK

    if not is_subscribed(user_id):
        return False, TKey.NEED_SUBSCRIPTION

    if decrease:
        if not check_and_increment_limit(user_id):
            return False, TKey.LIMIT_EXHAUSTED

    return True, TKey.STATUS_OK


# =========================
# ARTICLE SENDER
# =========================
def get_more_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔄", callback_data="more_random"))
    return kb


def send(chat_id, lang, query, more=False):
    cfg = Config(
        TELEGRAM_CHANNELS=[chat_id],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=query,
        LANG_CODE=lang,
        LAST_ARTICLE_FILE="",
        WITH_IMAGE=True,
    )

    article, ctx = get_article(cfg)

    if not article:
        bot.send_message(chat_id, "Error")
        return

    caption = get_caption(article, cfg.RULES_URL, ctx)
    kb = get_more_keyboard() if more else None

    if not article.image:
        bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=kb)
        return

    if article.image.desc.startswith("https://"):
        bot.send_photo(chat_id, article.image.desc,
                       caption=caption, parse_mode="HTML", reply_markup=kb)
        return

    with open(article.image.desc, "rb") as img:
        bot.send_photo(chat_id, img,
                       caption=caption, parse_mode="HTML", reply_markup=kb)


# =========================
# COMMAND REGISTRY
# =========================
COMMANDS = {}


def command(cmd):
    def wrapper(func):
        COMMANDS[cmd] = func
        return func

    return wrapper


def handle_command(message):
    text = (message.text or "").split()[0]

    for cmd_key, func in COMMANDS.items():
        if text.startswith(cmd_key):
            func(message)
            return

    if text == "/reborn":
        handle_reborn(message)
        return

    bot.send_message(message.chat.id, "Unknown command")


# =========================
# ROUTER (FSM CORE)
# =========================
@bot.message_handler(content_types=["text"])
def router(message):
    user_id = message.from_user.id
    text = (message.text or "").strip()

    if text.startswith("/"):
        handle_command(message)
        return

    state = get_state(user_id)

    if state == STATE_GET or state == STATE_NONE:
        handle_get_input(message)
        return


# =========================
# COMMANDS
# =========================
def ensure_user_lang(user_id: int, telegram_lang: str | None):
    with lang_lock:
        data = load_langs()
        key = str(user_id)

        if key not in data:
            data[key] = normalize_lang(telegram_lang)
            save_langs(data)


@command("/start")
def handle_start(message):
    ensure_user_lang(message.from_user.id, message.from_user.language_code)
    lang = get_user_lang(message.from_user.id, message.from_user.language_code)
    bot.send_message(message.chat.id, translate(lang, TKey.ABOUT))


@command(CMD_ABOUT)
def handle_about(message):
    lang = get_user_lang(message.from_user.id, message.from_user.language_code)
    bot.send_message(message.chat.id, translate(lang, TKey.ABOUT))


@command(CMD_STATUS)
def handle_status(message):
    lang = get_user_lang(message.from_user.id, message.from_user.language_code)
    bot.send_message(message.chat.id, translate(lang, TKey.STATUS_OK))


@command(CMD_LIMIT)
def handle_limit(message):
    data = load_limit()
    uid = str(message.from_user.id)
    used = data["users"].get(uid, 0)

    lang = get_user_lang(message.from_user.id, message.from_user.language_code)

    bot.send_message(
        message.chat.id,
        translate(lang, TKey.LIMIT_REMAINING, count=DAILY_USER_LIMIT - used)
    )


def get_lang_keyboard():
    kb = InlineKeyboardMarkup()

    buttons = []
    for lang in sorted(SUPPORTED_LANGS):
        buttons.append(InlineKeyboardButton(lang, callback_data=f"lang:{lang}"))

    row = []
    for i, b in enumerate(buttons, 1):
        row.append(b)
        if i % 4 == 0:
            kb.row(*row)
            row = []

    if row:
        kb.row(*row)

    return kb


@command(CMD_LANG)
def handle_lang(message):
    lang = get_user_lang(message.from_user.id, message.from_user.language_code)

    bot.send_message(
        message.chat.id,
        translate(lang, TKey.AVAILABLE_LANGS, values=", ".join(sorted(SUPPORTED_LANGS))),
        reply_markup=get_lang_keyboard()
    )


# =========================
# RANDOM
# =========================

@command(CMD_RANDOM)
def handle_random(message):
    uid = message.from_user.id
    lang = get_user_lang(uid, message.from_user.language_code)

    ok, reason = check_access(uid, decrease=True)

    if not ok:
        bot.send_message(message.chat.id, translate(lang, reason))
        return

    send(
        message.chat.id,
        lang,
        TRANSLATIONS[lang][TKey.RANDOM_FEATURED_PAGE],
        True
    )


# =========================
# GET FLOW (FSM)
# =========================
@command(CMD_GET)
def handle_get(message):
    uid = message.from_user.id
    lang = get_user_lang(uid, message.from_user.language_code)

    ok, reason = check_access(uid)

    if not ok:
        bot.send_message(message.chat.id, translate(lang, reason))
        return

    set_state(uid, STATE_GET)
    bot.send_message(message.chat.id, translate(lang, TKey.GET_PROMPT))


def handle_get_input(message):
    uid = message.from_user.id
    lang = get_user_lang(uid, message.from_user.language_code)
    text = (message.text or "").strip()

    try:
        ok, reason = check_access(uid, decrease=True)

        if not ok:
            bot.send_message(message.chat.id, translate(lang, reason))
            clear_state(uid)
            return

        send(message.chat.id, lang, text)

    except:
        bot.send_message(message.chat.id, translate(lang, TKey.GET_ERROR))

    finally:
        clear_state(uid)


# =========================
# CANCEL
# =========================
@command(CMD_CANCEL)
def handle_cancel(message):
    clear_state(message.from_user.id)

    lang = get_user_lang(message.from_user.id, message.from_user.language_code)
    bot.send_message(message.chat.id, translate(lang, TKey.CANCEL_OK))


# =========================
# CALLBACKS
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("lang:"))
def handle_lang_select(call):
    lang = call.data.split(":", 1)[1]

    set_user_lang(call.from_user.id, lang)
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=translate(normalize_lang(lang), TKey.LANG_CHANGED, value=lang)
    )


@bot.callback_query_handler(func=lambda c: c.data == "more_random")
def more(call):
    uid = call.from_user.id
    lang = get_user_lang(uid, call.from_user.language_code)

    ok, reason = check_access(uid, decrease=True)

    if not ok:
        bot.answer_callback_query(call.id, translate(lang, reason))
        return

    bot.answer_callback_query(call.id)
    send(call.message.chat.id, lang,
         TRANSLATIONS[lang][TKey.RANDOM_FEATURED_PAGE], True)


# =========================
# OWNER COMMANDS
# =========================
def handle_reborn(message):
    if message.from_user.id != OWNER_ID:
        return
    with limit_lock:
        data = load_limit()
        data["users"][str(OWNER_ID)] = 0
        save_limit(data)
    bot.send_message(message.chat.id, "Reborn OK")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)
    bot.infinity_polling()
