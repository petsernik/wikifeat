# now it's bad version, will be better
import os
from time import sleep

import telebot
from telebot import types

from config import TELEGRAM_BOT_TOKEN, OWNER_ID, Config, TMP_FOLDER_PATH
from core import run
from i18n import TKey, TRANSLATIONS

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


# ==== UI ====
def get_start_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Check status", callback_data="check_status"),
        types.InlineKeyboardButton("Random article", callback_data="random_article"),
    )
    return kb


def get_article_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🔄 Ещё", callback_data="random_article"),
        types.InlineKeyboardButton("✅ Status", callback_data="check_status"),
    )
    return kb


# ==== SEND LOGIC ====
def send(telegram_id: int|str):
    cfg = Config(
        TELEGRAM_CHANNELS=[telegram_id],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=TRANSLATIONS['ru'][TKey.RANDOM_FEATURED_PAGE],
        LANG_CODE='ru',
        LAST_ARTICLE_FILE=os.path.join(TMP_FOLDER_PATH, "last_article_test.txt"),
        WITH_IMAGE=True,
    )
    run(cfg)
    sleep(1)


# ==== HANDLERS ====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Press the button below",
        reply_markup=get_start_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == "check_status")
def handle_check_status(call):
    text = "status: ok"

    bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=get_start_keyboard()
    )

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "random_article")
def handle_random_article(call):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "no access", show_alert=True)
        return

    bot.answer_callback_query(call.id)

    # (опционально) убираем кнопки у старого сообщения
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
    except Exception:
        pass

    send(call.message.chat.id)


# ==== RUN ====
if __name__ == "__main__":
    bot.infinity_polling()