from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from config import PAGE_SIZE


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
