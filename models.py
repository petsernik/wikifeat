import json
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Any

from bs4 import Tag

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
        is_animation (bool): Анимация(гифка), если True, иначе изображение
    """
    desc: str
    licenses: List[str]
    page_url: str
    author_html: str
    is_animation: bool

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
    is_disambig: bool
    disambig_titles: list[str]

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
            "is_disambig": self.is_disambig,
            "disambig_titles": json.dumps(self.disambig_titles),
        }

    @staticmethod
    def from_db(row: Any, with_image: bool) -> "Article":
        """
        Восстановление из записи БД (asyncpg.Record).
        """

        image = None

        if row.get("image"):
            image_data = row["image"]
            if isinstance(image_data, str):
                image_data = json.loads(image_data)
            image = Image.from_dict(image_data) if with_image else None

        paragraphs = row["paragraphs"]
        if isinstance(paragraphs, str):
            paragraphs = json.loads(paragraphs)

        is_disambig = row.get("is_disambig", False)

        disambig_titles = row.get("disambig_titles")
        if disambig_titles is None:
            disambig_titles = []
        elif isinstance(disambig_titles, str):
            disambig_titles = json.loads(disambig_titles)

        return Article(
            title=row["title"],
            paragraphs=paragraphs,
            link=row["link"],
            image=image,
            is_disambig=is_disambig,
            disambig_titles=disambig_titles,
        )


@dataclass
class ArticleContext:
    lang: str
    url_or_title: str
    with_image: bool
    cached: bool

    def t(self, key: TKey, **kwargs) -> str:
        return translate(self.lang, key, **kwargs)


@dataclass
class ArticleContextRequest:
    ctx: ArticleContext
    url: str
    cached: bool


@dataclass(slots=True)
class ParagraphResult:
    paragraphs: list[str]
    is_disambig: bool = False
    titles: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParseResult:
    article: Article | None
    netloc: str | None
    main_block: Tag | None


@dataclass(slots=True)
class DisambigLevel:
    """
    Один уровень дизамбиг-UI.
    """
    titles: list[str]
    caption: str
    page: int = 0
    index: int = 0
    media: str | None = None
    media_is_animation: bool = False


@dataclass(slots=True)
class DisambigSession:
    """
    Модель состояния дизамбигов.
    """
    message_id: int

    levels: list[DisambigLevel] = field(default_factory=list)

    level_idx: int = 0
    page: int = 0
    index: int = 0

    # ---------- helpers ----------

    def current(self) -> DisambigLevel | None:
        if not self.levels:
            return None
        if self.level_idx < 0 or self.level_idx >= len(self.levels):
            return None
        return self.levels[self.level_idx]

    def push(self, level: DisambigLevel) -> None:
        """
        Вход в новый дизамбиг-уровень.
        """
        self.levels = self.levels[:self.level_idx + 1]

        self.levels.append(level)
        self.level_idx = len(self.levels) - 1
        self.page = 0
        self.index = 0

    def back(self) -> bool:
        """
        Возврат на уровень выше.
        """
        if self.level_idx <= 0:
            return False

        self.level_idx -= 1
        return True

    def set_index(self, idx: int, page_size: int) -> None:
        self.index = max(0, idx)
        self.page = self.index // page_size
