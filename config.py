import os
from dataclasses import dataclass
from typing import List

# получаем токен из переменной окружения
TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
TMP_FOLDER_PATH = 'tmp'
TEXT_IMAGE_PATH = os.path.join(TMP_FOLDER_PATH, 'image.jpg')
User_Agent = 'wikifeat/0.1 (https://github.com/petsernik/wikifeat)'


@dataclass
class Config:
    TELEGRAM_CHANNELS: List[str]
    RULES_URL: str
    WIKI_URL: str
    LAST_ARTICLE_FILE: str
