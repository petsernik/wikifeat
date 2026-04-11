from enum import Enum


class TKey(str, Enum):
    READ_ARTICLE = 'read_article'
    TEXT_LICENSE = 'text_license'

    IMAGE_LICENSE_SINGLE = 'image_license_single'
    IMAGE_LICENSE_MULTIPLE = 'image_license_multiple'

    AUTHOR_SINGLE = 'author_single'
    AUTHOR_MULTIPLE = 'author_multiple'
    AUTHOR_UNKNOWN = 'author_unknown'

    SOURCE_SINGLE = 'source_single'
    SOURCE_MULTIPLE = 'source_multiple'

    FAIR_USE = 'fair_use'
    PUBLIC_DOMAIN = 'public_domain'

    FONTS_AUTHOR = 'fonts_author'

    ARTICLE_NOT_CHANGED = 'article_not_changed'
    NEW_ARTICLE_SELECTED = 'new_article_selected'


TRANSLATIONS = {
    'ru': {
        TKey.READ_ARTICLE: 'Читать статью',
        TKey.TEXT_LICENSE: 'Лицензия на текст: CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Лицензия на изображение: {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Лицензии на изображение: {licenses}',

        TKey.AUTHOR_SINGLE: 'автор: {author}',
        TKey.AUTHOR_MULTIPLE: 'автор(ы): {author}',
        TKey.AUTHOR_UNKNOWN: 'автор неизвестен',

        TKey.SOURCE_SINGLE: 'источник: {source}',
        TKey.SOURCE_MULTIPLE: 'источник(и): {source}',

        TKey.FAIR_USE: 'Добросовестное использование',
        TKey.PUBLIC_DOMAIN: 'Общественное достояние',

        TKey.FONTS_AUTHOR: 'автор шрифта: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'Избранная статья не изменилась',
        TKey.NEW_ARTICLE_SELECTED: 'Избрана новая статья: {title}',
    },
    'en': {
        TKey.READ_ARTICLE: 'Read article',
        TKey.TEXT_LICENSE: 'Text license: CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Image license: {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Image licenses: {licenses}',

        TKey.AUTHOR_SINGLE: 'author: {author}',
        TKey.AUTHOR_MULTIPLE: 'author(s): {author}',
        TKey.AUTHOR_UNKNOWN: 'author unknown',

        TKey.SOURCE_SINGLE: 'source: {source}',
        TKey.SOURCE_MULTIPLE: 'source(s): {source}',

        TKey.FAIR_USE: 'Fair use',
        TKey.PUBLIC_DOMAIN: 'Public domain',

        TKey.FONTS_AUTHOR: 'font author: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'Featured article has not changed',
        TKey.NEW_ARTICLE_SELECTED: 'New featured article selected: {title}',
    }
}


def translate(lang: str, key: TKey, **kwargs) -> str:
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    template = lang_dict.get(key, key.value)
    return template.format(**kwargs)
