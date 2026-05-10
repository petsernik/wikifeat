from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def get_more_keyboard():
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄", callback_data="more_random")]
    ])
    return kb