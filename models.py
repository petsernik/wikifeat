import asyncio
import json
import re
import time
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Any

from bs4 import Tag
from telegram.error import TimedOut, NetworkError
from telegram.ext import Application
from telegram.request import HTTPXRequest
from httpx import ConnectError
from httpcore import ConnectError as CoreConnectError

from constants import PAGE_SIZE, TELEGRAM_BOT_TEST_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_PROXY
from i18n import TKey, translate, TRANSLATIONS


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
    langs = "|".join(map(re.escape, sorted(TRANSLATIONS.keys())))

    m = re.search(
        rf"\b({langs})\.wikipedia\.org\b",
        query,
        re.IGNORECASE,
    )
    if m:
        lang = m.group(1).lower()

    return Config(
        TELEGRAM_CHANNELS=[chat_id],
        RULES_URL="https://t.me/wikifeat/4",
        WIKI_URL_OR_NAME=query,
        LANG_CODE=lang,
    )


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

        level = self.levels[self.level_idx]

        # sync session state with current level
        self.index = level.index
        self.page = level.page

        return level

    def _sync_current(self) -> None:
        """
        Синхронизирует session.page/index
        с текущим уровнем.
        """
        level = self.current()
        if not level:
            return

        self.index = level.index
        self.page = level.page

    def push(self, level: DisambigLevel) -> None:
        """
        Вход в новый дизамбиг-уровень.
        """
        self.levels = self.levels[:self.level_idx + 1]

        self.levels.append(level)
        self.level_idx = len(self.levels) - 1

        self._sync_current()

    def back(self) -> bool:
        """
        Возврат на уровень выше.
        """
        if self.level_idx <= 0:
            return False

        self.level_idx -= 1

        self._sync_current()
        return True

    def set_index(self, idx: int) -> None:
        level = self.current()
        if not level:
            return

        level.index = max(0, idx)
        level.page = level.index // PAGE_SIZE

        self._sync_current()

    def shift(self, direction: str, cnt=1) -> bool:
        if direction == "prev":
            return self.left_shift(cnt)
        else:
            return self.right_shift(cnt)

    def left_shift(self, cnt=1) -> bool:
        """Сдвиг на cnt элементов влево в пределах текущего уровня."""
        level = self.current()
        if not level:
            return False

        if level.index >= cnt:
            level.index -= cnt
            level.page = level.index // PAGE_SIZE
            self._sync_current()
            return True

        return False

    def right_shift(self, cnt=1) -> bool:
        """Сдвиг на cnt элементов вправо в пределах текущего уровня."""
        level = self.current()
        if not level:
            return False

        if level.index < len(level.titles) - cnt:
            level.index += cnt
            level.page = level.index // PAGE_SIZE
            self._sync_current()
            return True

        return False

    def shift_page(self, direction: str) -> bool:
        if direction == "prev":
            return self.prev_page()
        else:
            return self.next_page()

    def prev_page(self) -> bool:
        """
        Переход на предыдущую страницу.

        Если вышли за границы текущего уровня —
        поднимаемся выше.
        """
        level = self.current()
        if not level:
            return False

        if level.page > 0:
            level.page -= 1
            level.index = level.page * PAGE_SIZE

            self._sync_current()
            return True

        return self.back()

    def next_page(self) -> bool:
        """
        Переход на следующую страницу.

        Если вышли за границы текущего уровня —
        поднимаемся выше.
        """
        level = self.current()
        if not level:
            return False

        max_page = (len(level.titles) - 1) // PAGE_SIZE

        if level.page < max_page:
            level.page += 1
            level.index = level.page * PAGE_SIZE

            self._sync_current()
            return True

        return self.back()


class LimitedHTTPStuckError(Exception):
    def __init__(self, cause: Exception):
        self.cause = cause
        super().__init__(f"HTTP stuck due to {type(cause).__name__}")


class LimitedHTTPXRequest(HTTPXRequest):
    def __init__(self, *args, max_concurrent, **kwargs):
        super().__init__(*args, **kwargs)

        self._sem = asyncio.Semaphore(max_concurrent)

        self.last_success = time.monotonic()

    async def do_request(self, *args, **kwargs):
        async with self._sem:
            for delay in (1, 2, 5):
                try:
                    result = await asyncio.wait_for(
                        super().do_request(*args, **kwargs),
                        timeout=15
                    )

                    self.last_success = time.monotonic()

                    return result

                except (TimedOut, NetworkError, ConnectError, CoreConnectError, asyncio.TimeoutError) as exc:
                    last_exc = exc
                    await asyncio.sleep(delay)

            raise LimitedHTTPStuckError(last_exc)


def get_app(is_test: bool = False) -> Application:
    token = (
        TELEGRAM_BOT_TEST_TOKEN
        if is_test
        else TELEGRAM_BOT_TOKEN
    )

    request = LimitedHTTPXRequest(
        connection_pool_size=100,
        read_timeout=10,
        write_timeout=10,
        connect_timeout=10,
        pool_timeout=5,
        max_concurrent=40,
        proxy=TELEGRAM_PROXY,
    )

    get_updates_request = LimitedHTTPXRequest(
        connection_pool_size=10,
        pool_timeout=30,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        max_concurrent=2,
        proxy=TELEGRAM_PROXY,
    )

    app = (
        Application.builder()
        .token(token)
        .arbitrary_callback_data(True)
        .request(request)
        .get_updates_request(get_updates_request)
        .build()
    )

    app.bot_data.update({
        "bot_request": request,
        "polling_request": get_updates_request,
        "watchdog_task": None,
    })

    return app
