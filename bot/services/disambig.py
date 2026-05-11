from bot.keyboards.disambig import build_disambig_keyboard
from models import DisambigSession


def get_session(context, message_id: int):
    return context.user_data.setdefault("disambig_sessions", {}).setdefault(
        message_id,
        DisambigSession(message_id=message_id)
    )


def get_disambig_keyboard_from_session(session: DisambigSession):
    level = session.current()
    if not level:
        return None

    return build_disambig_keyboard(level.titles, session.page)
