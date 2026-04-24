import os
from dataclasses import dataclass
from typing import List

# получаем токен из переменной окружения
TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
OWNER_ID = int(os.getenv("TELEGRAM_ID_OWNER", "0"))

TMP_FOLDER_PATH = 'tmp'
TEXT_IMAGE_PATH = os.path.join(TMP_FOLDER_PATH, 'image.jpg')

User_Agent = 'wikifeat/0.4 (https://github.com/petsernik/wikifeat)'

# ==== LIMITS ====
DAILY_TOTAL_LIMIT = 4900
DAILY_USER_LIMIT = 100

# ==== SPAM ====
SPAM_INTERVAL = 1.0

# ==== FILES ====
LIMIT_FILE = os.path.join(TMP_FOLDER_PATH, "daily_limit.json")

# ==== COMMANDS ====
CMD_STATUS = "/status"
CMD_RANDOM = "/random"
CMD_LIMIT = "/limit"
CMD_LANG = "/lang"
CMD_ABOUT = "/about"
CMD_DOWNLOAD = "/download"
CMD_CANCEL = "/cancel"


@dataclass
class Config:
    TELEGRAM_CHANNELS: List[str]
    RULES_URL: str
    LANG_CODE: str
    WIKI_URL_OR_NAME: str
    LAST_ARTICLE_FILE: str
    WITH_IMAGE: bool
