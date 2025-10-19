from dataclasses import dataclass
from typing import List

User_Agent = 'wikifeat/0.1 (https://github.com/petsernik/wikifeat)'


@dataclass
class Config:
    TELEGRAM_CHANNELS: List[str]
    RULES_URL: str
    WIKI_URL: str
    LAST_ARTICLE_FILE: str
