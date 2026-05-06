import asyncio
from typing import Tuple
from urllib.parse import urlparse

import aiohttp

from config import User_Agent
from db import get_skip_prefixes_from_db, save_skip_prefixes_to_db
from i18n import ADDITIONAL_TRANSLATIONS, TKey

# =========================
# CACHE (ONLY ONE)
# =========================

_skip_cache: dict[str, Tuple[str, ...]] = {}
_locks: dict[str, asyncio.Lock] = {}


# =========================
# FETCH FROM WIKIPEDIA
# =========================

async def fetch_skip_prefixes(lang: str) -> Tuple[str, ...]:
    url = f"https://{lang}.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "meta": "siteinfo",
        "siprop": "namespaces|namespacealiases",
        "format": "json"
    }

    headers = {"User-Agent": User_Agent}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

    namespaces = data["query"]["namespaces"]
    aliases = data["query"].get("namespacealiases", [])

    prefixes = set()

    for ns_id, ns in namespaces.items():
        if int(ns_id) == 0:
            continue

        name = ns.get("*")
        if name:
            prefixes.add(f"{name}:")

    for alias in aliases:
        name = alias.get("*")
        if name:
            prefixes.add(f"{name}:")

    # special namespaces
    prefixes.add("Special:")
    prefixes.add("Служебная:")

    return tuple(prefixes)


# =========================
# GET PREFIXES (DB + CACHE)
# =========================

async def get_skip_prefixes(lang: str) -> Tuple[str, ...]:
    # fast path
    if lang in _skip_cache:
        return _skip_cache[lang]

    lock = _locks.setdefault(lang, asyncio.Lock())

    async with lock:
        if lang in _skip_cache:
            return _skip_cache[lang]

        # DB
        prefixes = await get_skip_prefixes_from_db(lang)
        if prefixes:
            _skip_cache[lang] = prefixes
            return prefixes

        # API
        prefixes = await fetch_skip_prefixes(lang)

        # save
        await save_skip_prefixes_to_db(lang, prefixes)

        _skip_cache[lang] = prefixes
        return prefixes


# =========================
# HELPERS (i18n)
# =========================

def _get_meta(lang: str):
    tr = ADDITIONAL_TRANSLATIONS.get(lang, {})
    return tr.get(TKey.MAIN_PAGE), tr.get(TKey.TODAY_TEMPLATE)


def normalize_title(title: str) -> str:
    return title.replace("_", " ").strip()


# =========================
# VALIDATION
# =========================

async def is_valid_title(lang: str, title: str) -> bool:
    skip_prefixes = await get_skip_prefixes(lang)

    main_page, today_template = _get_meta(lang)

    title = normalize_title(title)
    # namespaces
    if any(title.startswith(p) for p in skip_prefixes):
        return False

    # main page
    if main_page and title == main_page:
        return False

    # today template
    if today_template and title == today_template:
        return False

    return True


async def is_article(lang: str, url: str) -> bool:
    path = urlparse(url).path
    if "/wiki/" not in path:
        return False

    title = path.split("/wiki/")[-1]
    return await is_valid_title(lang, title)
