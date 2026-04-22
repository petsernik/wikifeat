import os
from dataclasses import dataclass
from typing import List

# получаем токен из переменной окружения
TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
OWNER_ID = int(os.getenv("TELEGRAM_ID_OWNER", "0"))
TMP_FOLDER_PATH = 'tmp'
TEXT_IMAGE_PATH = os.path.join(TMP_FOLDER_PATH, 'image.jpg')
User_Agent = 'wikifeat/0.32 (https://github.com/petsernik/wikifeat)'


@dataclass
class Config:
    TELEGRAM_CHANNELS: List[str]
    RULES_URL: str
    LANG_CODE: str
    WIKI_URL_OR_NAME: str
    LAST_ARTICLE_FILE: str
    WITH_IMAGE: bool
