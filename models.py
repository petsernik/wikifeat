from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FeaturedArticle:
    title: str
    paragraphs: List[str]
    image_url: Optional[str]
    link: str
    image_licenses: List[str]
    image_page_url: Optional[str]
    author_html: Optional[str]
