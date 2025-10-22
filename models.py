from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Image:
    url: str
    licenses: List[str]
    page_url: str
    author_html: str


@dataclass
class Article:
    title: str
    paragraphs: List[str]
    link: str
    image: Optional[Image]
