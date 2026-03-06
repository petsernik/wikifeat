from dataclasses import dataclass
from typing import List, Optional


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
