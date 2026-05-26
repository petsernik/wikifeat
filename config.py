import os
from dataclasses import dataclass
from typing import List

TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
TELEGRAM_BOT_TEST_TOKEN = os.environ.get('WIKIFEATTESTTOKEN')
OWNER_ID = int(os.getenv("TELEGRAM_ID_OWNER", "0"))

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(DIR_PATH, "Renju.otf")
SELF_MADE_IMAGE_CASE = "If this appears in an exception, generate the image manually for this case."

CHANNEL_USERNAME = "@wikifeat"
User_Agent = 'wikifeat/0.52 (https://github.com/petsernik/wikifeat)'

PAGE_SIZE = 8

# ==== LIMITS ====
DAILY_TOTAL_LIMIT = 4900
DAILY_USER_LIMIT = 100

# ==== SPAM ====
SPAM_INTERVAL = 0.1

# ==== COMMANDS ====
CMD_STATUS = "status"
CMD_RANDOM = "random"
CMD_GET = "get"
CMD_CANCEL = "cancel"
CMD_LIMIT = "limit"
CMD_LANG = "lang"
CMD_ABOUT = "about"
CMD_UPDATE = "update"

# ==== POSTGRES PARAMETERS ====
DB_USER = 'postgres'
DB_PASSWORD = os.environ.get('POSTGRES_DB_PASSWORD')
DB_NAME = 'wikifeat'
DB_TEST_NAME = 'wikifeattest'
DB_HOST = '127.0.0.1'
DB_MIN_SIZE = 1
DB_MAX_SIZE = 10

INIT_SQL_PATH = os.path.join(DIR_PATH, 'schema.sql')


@dataclass
class Config:
    TELEGRAM_CHANNELS: List[str]
    RULES_URL: str
    LANG_CODE: str
    WIKI_URL_OR_NAME: str
    WITH_IMAGE: bool = True
    USE_AND_UPDATE_LAST_FEATURED_TITLE: bool = False
    USE_CACHE_FOR_GETTING_CONTEXT_REQ: bool = True
    SAVE_ARTICLE_TO_DB: bool = True


async def get_config(chat_id, query, lang) -> Config:
    return Config(
        TELEGRAM_CHANNELS=[chat_id],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=query,
        LANG_CODE=lang,
    )
