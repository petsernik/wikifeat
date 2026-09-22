from db import get_lang, set_lang
from utils import normalize_lang


async def get_user_lang(user_id: int, tg_lang: str | None):
    lang = await get_lang(user_id)
    if lang:
        return lang
    return await set_user_lang(user_id, tg_lang)

async def set_user_lang(user_id: int, lang: str) -> str:
    lang = normalize_lang(lang)
    await set_lang(user_id, lang)
    return lang