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
    CMD_STATUS, CMD_RANDOM, CMD_LIMIT, CMD_LANG, CMD_ABOUT
)
from core import get_article, get_caption
from i18n import TKey, TRANSLATIONS, translate

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

limit_lock = threading.Lock()
user_last_request_time = {}

CHANNEL_USERNAME = "@wikifeat"

LANG_FILE = os.path.join(TMP_FOLDER_PATH, "user_lang.json")
lang_lock = threading.Lock()

SUPPORTED_LANGS = {"ru", "en", "de", "fr", "es", "it", "pt", "pl", "be", "kk"}


# =========================
# CMD HELPER
# =========================
def cmd(c: str) -> str:
    return c.lstrip('/')


# =========================
# LANG SYSTEM (fallback + telegram locale)
# =========================
def normalize_lang(code: str | None) -> str:
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


def get_user_lang(user_id: int, telegram_lang: str | None = None) -> str:
    data = load_langs()

    if str(user_id) in data:
        return data[str(user_id)]

    return normalize_lang(telegram_lang)


def set_user_lang(user_id: int, lang: str):
    lang = normalize_lang(lang)

    with lang_lock:
        data = load_langs()
        data[str(user_id)] = lang
        save_langs(data)


def ensure_user_lang(user_id: int, telegram_lang: str | None):
    data = load_langs()
    key = str(user_id)

    if key not in data:
        data[key] = normalize_lang(telegram_lang)
        save_langs(data)


# =========================
# SUBSCRIPTION
# =========================
def is_subscribed(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


# =========================
# INLINE BUTTON
# =========================
def get_more_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄", callback_data="more_random"))
    return markup


# =========================
# LIMIT + SPAM
# =========================
def load_limit():
    if not os.path.exists(LIMIT_FILE):
        return {"date": None, "total": 0, "users": {}}

    try:
        with open(LIMIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"date": None, "total": 0, "users": {}}


def save_limit_atomic(data):
    tmp_file = LIMIT_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp_file, LIMIT_FILE)


def get_today():
    return datetime.now(UTC).strftime("%Y-%m-%d")


def get_limit_state():
    with limit_lock:
        today = get_today()
        data = load_limit()

        if data["date"] != today:
            return {"date": today, "total": 0, "users": {}}

        return data


def check_and_increment_limit(user_id: int):
    with limit_lock:
        today = get_today()
        data = load_limit()

        if data["date"] != today:
            data = {"date": today, "total": 0, "users": {}}

        if data["total"] >= DAILY_TOTAL_LIMIT:
            return False, "global_limit"

        user_key = str(user_id)
        user_count = data["users"].get(user_key, 0)

        if user_count >= DAILY_USER_LIMIT:
            return False, "user_limit"

        data["total"] += 1
        data["users"][user_key] = user_count + 1

        save_limit_atomic(data)
        return True, "ok"


def is_spam(user_id: int) -> bool:
    now = time.time()
    last = user_last_request_time.get(user_id, 0)

    if now - last < SPAM_INTERVAL:
        return True

    user_last_request_time[user_id] = now
    return False


# =========================
# SEND
# =========================
def send(chat_id: int | str, lang: str):
    cfg = Config(
        TELEGRAM_CHANNELS=[chat_id],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=TRANSLATIONS[lang][TKey.RANDOM_FEATURED_PAGE],
        LANG_CODE=lang,
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, "last_article_test.txt"),
        WITH_IMAGE=True,
    )

    article, ctx = get_article(cfg)

    if not article:
        bot.send_message(chat_id, "Error")
        return

    caption = get_caption(article, cfg.RULES_URL, ctx)
    keyboard = get_more_keyboard()

    if not article.image:
        bot.send_message(chat_id, caption, parse_mode='HTML', reply_markup=keyboard)
        return

    if article.image.desc.startswith('https://'):
        bot.send_photo(chat_id, article.image.desc, caption=caption,
                       parse_mode='HTML', reply_markup=keyboard)
        return

    with open(article.image.desc, 'rb') as img:
        bot.send_photo(chat_id, img, caption=caption,
                       parse_mode='HTML', reply_markup=keyboard)


# =========================
# COMMANDS
# =========================
def start_text(lang: str):
    return translate(lang, TKey.START_COMMANDS)


@bot.message_handler(commands=['start', cmd(CMD_ABOUT)])
def handle_start_about(message):
    ensure_user_lang(message.from_user.id, message.from_user.language_code)
    lang = get_user_lang(message.from_user.id, message.from_user.language_code)
    bot.send_message(message.chat.id, start_text(lang))


@bot.message_handler(commands=[cmd(CMD_STATUS)])
def handle_status(message):
    lang = get_user_lang(message.from_user.id, message.from_user.language_code)
    bot.send_message(message.chat.id, translate(lang, TKey.STATUS_OK))


@bot.message_handler(commands=[cmd(CMD_LIMIT)])
def handle_limit(message):
    lang = get_user_lang(message.from_user.id, message.from_user.language_code)

    data = get_limit_state()
    user_key = str(message.from_user.id)
    user_count = data["users"].get(user_key, 0)

    remaining = max(0, DAILY_USER_LIMIT - user_count)

    bot.send_message(
        message.chat.id,
        translate(lang, TKey.LIMIT_REMAINING, count=remaining)
    )


# =========================
# LANG COMMAND
# =========================
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


@bot.message_handler(commands=[cmd(CMD_LANG)])
def handle_lang(message):
    lang = get_user_lang(message.from_user.id, message.from_user.language_code)

    bot.send_message(
        message.chat.id,
        translate(lang, TKey.AVAILABLE_LANGS, values=", ".join(sorted(SUPPORTED_LANGS))),
        reply_markup=get_lang_keyboard()
    )


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


# =========================
# RANDOM
# =========================
@bot.message_handler(commands=[cmd(CMD_RANDOM)])
def handle_random(message):
    user_id = message.from_user.id
    lang = get_user_lang(user_id, message.from_user.language_code)

    if is_spam(user_id):
        bot.send_message(message.chat.id, translate(lang, TKey.SPAM_BLOCK))
        return

    if not is_subscribed(user_id):
        bot.send_message(message.chat.id, translate(lang, TKey.NEED_SUBSCRIPTION))
        return

    allowed, reason = check_and_increment_limit(user_id)

    if not allowed:
        bot.send_message(message.chat.id, translate(lang, TKey.LIMIT_EXHAUSTED))
        return

    send(message.chat.id, lang)


# =========================
# CALLBACK
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "more_random")
def handle_more(call):
    user_id = call.from_user.id
    lang = get_user_lang(user_id, call.from_user.language_code)

    if is_spam(user_id):
        bot.answer_callback_query(call.id, "Too fast")
        return

    allowed, reason = check_and_increment_limit(user_id)

    if not allowed:
        bot.answer_callback_query(call.id, "Limit")
        return

    bot.answer_callback_query(call.id)
    send(call.message.chat.id, lang)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)
    bot.infinity_polling()
