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

    MAIN_PAGE = 'main_page'


# ISO 639-1
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

        TKey.MAIN_PAGE: 'Заглавная страница',
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

        TKey.MAIN_PAGE: 'Main Page',
    },

    'fr': {
        TKey.READ_ARTICLE: 'Lire l’article',
        TKey.TEXT_LICENSE: 'Licence du texte : CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Licence de l’image : {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Licences des images : {licenses}',

        TKey.AUTHOR_SINGLE: 'auteur : {author}',
        TKey.AUTHOR_MULTIPLE: 'auteurs : {author}',
        TKey.AUTHOR_UNKNOWN: 'auteur inconnu',

        TKey.SOURCE_SINGLE: 'source : {source}',
        TKey.SOURCE_MULTIPLE: 'sources : {source}',

        TKey.FAIR_USE: 'Usage équitable',
        TKey.PUBLIC_DOMAIN: 'Domaine public',

        TKey.FONTS_AUTHOR: 'auteur de la police : {author}',

        TKey.ARTICLE_NOT_CHANGED: "L'article vedette n'a pas changé",
        TKey.NEW_ARTICLE_SELECTED: 'Nouvel article vedette sélectionné : {title}',

        TKey.MAIN_PAGE: 'Wikipédia:Accueil principal',
    },

    'de': {
        TKey.READ_ARTICLE: 'Artikel lesen',
        TKey.TEXT_LICENSE: 'Textlizenz: CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Bildlizenz: {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Bildlizenzen: {licenses}',

        TKey.AUTHOR_SINGLE: 'Autor: {author}',
        TKey.AUTHOR_MULTIPLE: 'Autoren: {author}',
        TKey.AUTHOR_UNKNOWN: 'Autor unbekannt',

        TKey.SOURCE_SINGLE: 'Quelle: {source}',
        TKey.SOURCE_MULTIPLE: 'Quellen: {source}',

        TKey.FAIR_USE: 'Fair Use',
        TKey.PUBLIC_DOMAIN: 'Gemeinfrei',

        TKey.FONTS_AUTHOR: 'Schriftautor: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'Ausgewählter Artikel hat sich nicht geändert',
        TKey.NEW_ARTICLE_SELECTED: 'Neuer ausgewählter Artikel: {title}',

        TKey.MAIN_PAGE: 'Wikipedia:Hauptseite',
    },

    'es': {
        TKey.READ_ARTICLE: 'Leer artículo',
        TKey.TEXT_LICENSE: 'Licencia del texto: CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Licencia de imagen: {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Licencias de imagen: {licenses}',

        TKey.AUTHOR_SINGLE: 'autor: {author}',
        TKey.AUTHOR_MULTIPLE: 'autores: {author}',
        TKey.AUTHOR_UNKNOWN: 'autor desconocido',

        TKey.SOURCE_SINGLE: 'fuente: {source}',
        TKey.SOURCE_MULTIPLE: 'fuentes: {source}',

        TKey.FAIR_USE: 'Uso legítimo',
        TKey.PUBLIC_DOMAIN: 'Dominio público',

        TKey.FONTS_AUTHOR: 'autor de la fuente: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'El artículo destacado no ha cambiado',
        TKey.NEW_ARTICLE_SELECTED: 'Nuevo artículo destacado seleccionado: {title}',

        TKey.MAIN_PAGE: 'Wikipedia:Portada',
    },

    'it': {
        TKey.READ_ARTICLE: 'Leggi articolo',
        TKey.TEXT_LICENSE: 'Licenza del testo: CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Licenza immagine: {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Licenze immagini: {licenses}',

        TKey.AUTHOR_SINGLE: 'autore: {author}',
        TKey.AUTHOR_MULTIPLE: 'autori: {author}',
        TKey.AUTHOR_UNKNOWN: 'autore sconosciuto',

        TKey.SOURCE_SINGLE: 'fonte: {source}',
        TKey.SOURCE_MULTIPLE: 'fonti: {source}',

        TKey.FAIR_USE: 'Uso corretto',
        TKey.PUBLIC_DOMAIN: 'Dominio pubblico',

        TKey.FONTS_AUTHOR: 'autore del font: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'L’articolo in evidenza non è cambiato',
        TKey.NEW_ARTICLE_SELECTED: 'Nuovo articolo in evidenza selezionato: {title}',

        TKey.MAIN_PAGE: 'Pagina principale',
    },

    'pt': {
        TKey.READ_ARTICLE: 'Ler artigo',
        TKey.TEXT_LICENSE: 'Licença do texto: CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Licença da imagem: {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Licenças das imagens: {licenses}',

        TKey.AUTHOR_SINGLE: 'autor: {author}',
        TKey.AUTHOR_MULTIPLE: 'autores: {author}',
        TKey.AUTHOR_UNKNOWN: 'autor desconhecido',

        TKey.SOURCE_SINGLE: 'fonte: {source}',
        TKey.SOURCE_MULTIPLE: 'fontes: {source}',

        TKey.FAIR_USE: 'Uso justo',
        TKey.PUBLIC_DOMAIN: 'Domínio público',

        TKey.FONTS_AUTHOR: 'autor da fonte: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'O artigo em destaque não mudou',
        TKey.NEW_ARTICLE_SELECTED: 'Novo artigo em destaque selecionado: {title}',

        TKey.MAIN_PAGE: 'Wikipédia:Página_principal',
    },

    'pl': {
        TKey.READ_ARTICLE: 'Czytaj artykuł',
        TKey.TEXT_LICENSE: 'Licencja tekstu: CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Licencja obrazu: {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Licencje obrazów: {licenses}',

        TKey.AUTHOR_SINGLE: 'autor: {author}',
        TKey.AUTHOR_MULTIPLE: 'autorzy: {author}',
        TKey.AUTHOR_UNKNOWN: 'autor nieznany',

        TKey.SOURCE_SINGLE: 'źródło: {source}',
        TKey.SOURCE_MULTIPLE: 'źródła: {source}',

        TKey.FAIR_USE: 'Dozwolony użytek',
        TKey.PUBLIC_DOMAIN: 'Domena publiczna',

        TKey.FONTS_AUTHOR: 'autor czcionki: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'Wyróżniony artykuł nie zmienił się',
        TKey.NEW_ARTICLE_SELECTED: 'Wybrano nowy wyróżniony artykuł: {title}',

        TKey.MAIN_PAGE: 'Wikipedia:Strona główna',
    },

    'be': {
        TKey.READ_ARTICLE: 'Чытаць артыкул',
        TKey.TEXT_LICENSE: 'Ліцэнзія тэксту: CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Ліцэнзія выявы: {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Ліцэнзіі выяў: {licenses}',

        TKey.AUTHOR_SINGLE: 'аўтар: {author}',
        TKey.AUTHOR_MULTIPLE: 'аўтары: {author}',
        TKey.AUTHOR_UNKNOWN: 'аўтар невядомы',

        TKey.SOURCE_SINGLE: 'крыніца: {source}',
        TKey.SOURCE_MULTIPLE: 'крыніцы: {source}',

        TKey.FAIR_USE: 'Сумленнае выкарыстанне',
        TKey.PUBLIC_DOMAIN: 'Грамадскі набытак',

        TKey.FONTS_AUTHOR: 'аўтар шрыфту: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'Выбраны артыкул не змяніўся',
        TKey.NEW_ARTICLE_SELECTED: 'Абраны новы артыкул: {title}',

        TKey.MAIN_PAGE: 'Галоўная старонка',
    },

    'kk': {
        TKey.READ_ARTICLE: 'Мақаланы оқу',
        TKey.TEXT_LICENSE: 'Мәтін лицензиясы: CC BY-SA',

        TKey.IMAGE_LICENSE_SINGLE: 'Сурет лицензиясы: {license}',
        TKey.IMAGE_LICENSE_MULTIPLE: 'Сурет лицензиялары: {licenses}',

        TKey.AUTHOR_SINGLE: 'автор: {author}',
        TKey.AUTHOR_MULTIPLE: 'авторлар: {author}',
        TKey.AUTHOR_UNKNOWN: 'авторы белгісіз',

        TKey.SOURCE_SINGLE: 'дереккөз: {source}',
        TKey.SOURCE_MULTIPLE: 'дереккөздер: {source}',

        TKey.FAIR_USE: 'Әділ пайдалану',
        TKey.PUBLIC_DOMAIN: 'Қоғамдық игілік',

        TKey.FONTS_AUTHOR: 'қаріп авторы: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'Таңдалған мақала өзгерген жоқ',
        TKey.NEW_ARTICLE_SELECTED: 'Жаңа таңдалған мақала: {title}',

        TKey.MAIN_PAGE: 'Басты бет',
    },
}


def translate(lang: str, key: TKey, **kwargs) -> str:
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    template = lang_dict.get(key, key.value)
    return template.format(**kwargs)
