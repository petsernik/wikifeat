from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from i18n import TRANSLATIONS


def get_lang_keyboard():
    buttons = [
        InlineKeyboardButton(lang, callback_data=f"lang:{lang}")
        for lang in sorted(TRANSLATIONS.keys())
    ]

    rows = [buttons[i:i + 4] for i in range(0, len(buttons), 4)]
    return InlineKeyboardMarkup(rows)