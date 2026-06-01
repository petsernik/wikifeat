from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from i18n import translate, TKey


def get_more_random_keyboard():
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄", callback_data="more_random")]
    ])
    return kb


def get_retry_keyboard(lang: str, title: str, request_type: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                translate(lang, TKey.TRY_AGAIN_THIS_PAGE),
                callback_data=f"try_again|{request_type}|{title}",
            )
        ],
        [
            InlineKeyboardButton("❌", callback_data="delete"),
            InlineKeyboardButton("🔄", callback_data="more_random"),
        ]
    ])
