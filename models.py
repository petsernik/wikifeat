import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Any

from i18n import TKey, translate


@dataclass
class Image:
    """
    Структура данных, описывающая изображение и связанную с ним
    лицензионную и атрибуционную информацию.

    Используется для хранения метаданных изображения, полученных
    со страницы Википедии или другого источника.

    Attributes:
        desc (str): Описание изображения (file_id Telegram, HTTP URL или локальный путь).
        licenses (List[str]): Список сокращенных названий лицензий (например, ['CC-BY-SA', 'GFDL']).
        page_url (str): Ссылка на страницу с полной информацией о медиафайле.
        author_html (str): Строка в формате HTML для корректного отображения авторства.
    """
    desc: str
    licenses: List[str]
    page_url: str
    author_html: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Image":
        return Image(**data)


@dataclass
class Article:
    """
    Структура данных, представляющая статью с текстовым содержимым
    и опционально связанным изображением.

    Используется для хранения преамбулы статьи, полученной из Википедии
    или другого текстового источника.

    Attributes:
        title (str): Заголовок статьи.
        paragraphs (List[str]): Список абзацев статьи в порядке следования.
        link (str): URL статьи или каноническая ссылка на источник.
        image (Optional[Image]): Объект изображения или None, если оно отсутствует.
    """
    title: str
    paragraphs: List[str]
    link: str
    image: Optional[Image]

    # ---------- DB serialization ----------

    def to_db(self) -> dict:
        """
        Подготовка к сохранению в PostgreSQL.
        """
        return {
            "title": self.title,
            "paragraphs": json.dumps(self.paragraphs),
            "link": self.link,
            "image": json.dumps(self.image.to_dict()) if self.image else None,
        }

    @staticmethod
    def from_db(row: Any) -> "Article":
        """
        Восстановление из записи БД (asyncpg.Record).
        """
        image = None

        if row["image"]:
            image_data = row["image"]
            if isinstance(image_data, str):
                image_data = json.loads(image_data)
            image = Image.from_dict(image_data)

        paragraphs = row["paragraphs"]
        if isinstance(paragraphs, str):
            paragraphs = json.loads(paragraphs)

        return Article(
            title=row["title"],
            paragraphs=paragraphs,
            link=row["link"],
            image=image,
        )


@dataclass
class ArticleContext:
    lang: str
    url_or_name: str
    with_image: bool
    cached: bool

    def t(self, key: TKey, **kwargs) -> str:
        return translate(self.lang, key, **kwargs)


@dataclass
class ArticleContextRequest:
    ctx: ArticleContext
    url: str
    cached: bool
