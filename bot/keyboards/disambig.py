from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from constants import PAGE_SIZE


def build_disambig_keyboard(links: list[str], page: int = 0):
    start = page * PAGE_SIZE
    chunk = links[start:start + PAGE_SIZE]

    max_page = max(0, (len(links) - 1) // PAGE_SIZE)

    keyboard = [
        [InlineKeyboardButton(text=link, callback_data=f"open|{start + i}")]
        for i, link in enumerate(chunk)
    ]

    nav = [
        InlineKeyboardButton(
            "⬅️",
            callback_data="page|prev"
        ),
        InlineKeyboardButton("↩️", callback_data="back"),
        InlineKeyboardButton(
            "➡️",
            callback_data="page|next"
        ),
    ]
    keyboard.append(nav)

    return InlineKeyboardMarkup(keyboard)


def build_disambig_nav_keyboard(idx: int, total: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️",
                callback_data="nav|prev"
            ),
            InlineKeyboardButton("↩️", callback_data="back_nav"),
            InlineKeyboardButton(
                "➡️",
                callback_data="nav|next"
            ),
        ]
    ])
