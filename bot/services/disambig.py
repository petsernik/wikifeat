from bot.keyboards.disambig import build_disambig_keyboard
from config import PAGE_SIZE
from models import DisambigSession


def get_session(context, message_id: int):
    return context.user_data.setdefault("disambig_sessions", {}).setdefault(
        message_id,
        DisambigSession(message_id=message_id)
    )


def clamp_page(page: int, total: int) -> int:
    max_page = max(0, (total - 1) // PAGE_SIZE)
    return max(0, min(page, max_page))

def get_disambig_keyboard_from_session(session: DisambigSession):
    level = session.current()
    if not level:
        return None

    return build_disambig_keyboard(level.titles, session.page)
