from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from i18n import TKey, translate


def build_reading_keyboard(lang: str, title: str, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для режима чтения статьи.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"reading|{current_page - 1}|{lang}|{title}" if current_page > 0 else "noop"
            ),
            InlineKeyboardButton(
                "↩️",
                callback_data=f"reading|back|{lang}|{title}"
            ),
            InlineKeyboardButton(
                "➡️",
                callback_data=f"reading|{current_page + 1}|{lang}|{title}" if current_page < total_pages - 1 else "noop"
            ),
        ]
    ]

    # Добавляем индикатор страницы, если есть больше одной страницы
    if total_pages > 1:
        keyboard.insert(0, [
            InlineKeyboardButton(
                f"{current_page + 1}/{total_pages}",
                callback_data="reading|page_info"
            )
        ])

    return InlineKeyboardMarkup(keyboard)


def build_article_keyboard_with_reading_button(lang: str, title: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для статьи с кнопкой "Читать статью здесь".
    """
    keyboard = [
        [
            InlineKeyboardButton(
                translate(lang, TKey.READ_ARTICLE_HERE),
                callback_data=f"reading|start|{lang}|{title}"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)
