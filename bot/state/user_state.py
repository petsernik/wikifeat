from typing import Dict

STATE_NONE = "none"
STATE_GET = "get"
STATE_UPDATE = "update"

user_state: Dict[int, str] = {}


def get_state(user_id: int):
    return user_state.get(user_id, STATE_NONE)


def set_state(user_id: int, state: str):
    user_state[user_id] = state


def clear_state(user_id: int):
    user_state[user_id] = STATE_NONE
