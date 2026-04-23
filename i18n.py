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
    TODAY_TEMPLATE = 'TODAY_TEMPLATE'
    RANDOM_FEATURED_PAGE = 'random_featured_page'

    # UX
    START_COMMANDS = 'start_commands'
    SPAM_BLOCK = 'spam_block'
    LIMIT_REMAINING = 'limit_remaining'
    LIMIT_EXHAUSTED = 'limit_exhausted'
    NEED_SUBSCRIPTION = 'need_subscription'
    STATUS_OK = 'status_ok'
    LANG_CHANGED = 'lang_changed'
    AVAILABLE_LANGS = 'available_langs'


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

        TKey.FAIR_USE: 'Добрасумленнае выкарыстанне',
        TKey.PUBLIC_DOMAIN: 'Грамадскі набытак',

        TKey.FONTS_AUTHOR: 'аўтар шрыфту: {author}',

        TKey.ARTICLE_NOT_CHANGED: 'Выбраны артыкул не змяніўся',
        TKey.NEW_ARTICLE_SELECTED: 'Абраны новы артыкул: {title}',
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
    },
}

# Categories from https://www.wikidata.org/wiki/Q4387444, THANKS :)
ADDITIONAL_TRANSLATIONS = {
    'ru': {
        TKey.MAIN_PAGE: 'Заглавная страница',
        TKey.TODAY_TEMPLATE: 'Шаблон:Текущая избранная статья',
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Категория:Википедия:Избранные_статьи_по_алфавиту',
    },
    'en': {
        TKey.MAIN_PAGE: 'Main Page',
        TKey.TODAY_TEMPLATE: "Wikipedia:Today's featured article",
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Category:Featured articles',
    },
    'fr': {
        TKey.MAIN_PAGE: 'Wikipédia:Accueil principal',
        TKey.TODAY_TEMPLATE: '',
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Catégorie:Article de qualité',
    },
    'de': {
        TKey.MAIN_PAGE: 'Wikipedia:Hauptseite',
        TKey.TODAY_TEMPLATE: '',
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Kategorie:Wikipedia:Exzellent',
    },
    'es': {
        TKey.MAIN_PAGE: 'Wikipedia:Portada',
        TKey.TODAY_TEMPLATE: '',
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Categoría:Wikipedia:Artículos destacados',
    },
    'it': {
        TKey.MAIN_PAGE: 'Pagina principale',
        TKey.TODAY_TEMPLATE: '',
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Categoria:Voci_in_vetrina_su_it.wiki',
    },
    'pt': {
        TKey.MAIN_PAGE: 'Wikipédia:Página_principal',
        TKey.TODAY_TEMPLATE: '',
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Categoria:!Artigos destacados',
    },
    'pl': {
        TKey.MAIN_PAGE: 'Wikipedia:Strona główna',
        TKey.TODAY_TEMPLATE: '',
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Kategoria:Artykuły na Medal',
    },
    'be': {
        TKey.MAIN_PAGE: 'Галоўная старонка',
        TKey.TODAY_TEMPLATE: '',
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Катэгорыя:Вікіпедыя:Выдатныя артыкулы паводле алфавіта',
    },
    'kk': {
        TKey.MAIN_PAGE: 'Басты бет',
        TKey.TODAY_TEMPLATE: '',
        TKey.RANDOM_FEATURED_PAGE: 'Special:RandomInCategory/Санат:Уикипедия:Алфавит бойынша таңдаулы мақалалар',
    },
}

for lang, data in ADDITIONAL_TRANSLATIONS.items():
    TRANSLATIONS.setdefault(lang, {}).update(data)

BOT_TRANSLATIONS = {
    'ru': {
        TKey.START_COMMANDS: (
            "Доступные команды:\n"
            "/status — проверить статус\n"
            "/random — получить случайную статью\n"
            "/limit — посмотреть оставшийся лимит\n"
            "/lang — выбрать язык (choose language)\n"
            "/info — информация"
        ),
        TKey.SPAM_BLOCK: 'Слишком частые запросы.',
        TKey.LIMIT_REMAINING: 'Осталось запросов: {count}',
        TKey.LIMIT_EXHAUSTED: 'Суточный лимит исчерпан.',
        TKey.NEED_SUBSCRIPTION: 'Для доступа нужно подписаться на @wikifeat.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Язык изменён: {value}',
        TKey.AVAILABLE_LANGS: 'Доступные языки: {values}',
    },

    'en': {
        TKey.START_COMMANDS: (
            "Available commands:\n"
            "/status — check status\n"
            "/random — get random article\n"
            "/limit — check remaining limit\n"
            "/lang — choose language\n"
            "/info — info"
        ),
        TKey.SPAM_BLOCK: 'Too many requests.',
        TKey.LIMIT_REMAINING: 'Requests remaining: {count}',
        TKey.LIMIT_EXHAUSTED: 'Daily limit exceeded.',
        TKey.NEED_SUBSCRIPTION: 'You need to subscribe to @wikifeat.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Language changed: {value}',
        TKey.AVAILABLE_LANGS: 'Available languages: {values}',
    },

    'de': {
        TKey.START_COMMANDS: (
            "Verfügbare Befehle:\n"
            "/status — Status prüfen\n"
            "/random — zufälligen Artikel erhalten\n"
            "/limit — verbleibendes Limit\n"
            "/lang — Sprache wählen (choose language)\n"
            "/info — Info"
        ),
        TKey.SPAM_BLOCK: 'Zu viele Anfragen.',
        TKey.LIMIT_REMAINING: 'Verbleibende Anfragen: {count}',
        TKey.LIMIT_EXHAUSTED: 'Tageslimit erreicht.',
        TKey.NEED_SUBSCRIPTION: 'Abonniere @wikifeat für Zugriff.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Sprache geändert: {value}',
        TKey.AVAILABLE_LANGS: 'Verfügbare Sprachen: {values}',
    },

    'fr': {
        TKey.START_COMMANDS: (
            "Commandes disponibles:\n"
            "/status — vérifier le statut\n"
            "/random — article aléatoire\n"
            "/limit — limite restante\n"
            "/lang — choisir la langue (choose language)\n"
            "/info — info"
        ),
        TKey.SPAM_BLOCK: 'Trop de requêtes.',
        TKey.LIMIT_REMAINING: 'Requêtes restantes : {count}',
        TKey.LIMIT_EXHAUSTED: 'Limite quotidienne atteinte.',
        TKey.NEED_SUBSCRIPTION: 'Abonnez-vous à @wikifeat.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Langue changée : {value}',
        TKey.AVAILABLE_LANGS: 'Langues disponibles : {values}',
    },

    'es': {
        TKey.START_COMMANDS: (
            "Comandos disponibles:\n"
            "/status — comprobar estado\n"
            "/random — artículo aleatorio\n"
            "/limit — límite restante\n"
            "/lang — elegir idioma (choose language)\n"
            "/info — info"
        ),
        TKey.SPAM_BLOCK: 'Demasiadas solicitudes.',
        TKey.LIMIT_REMAINING: 'Solicitudes restantes: {count}',
        TKey.LIMIT_EXHAUSTED: 'Límite diario alcanzado.',
        TKey.NEED_SUBSCRIPTION: 'Suscríbete a @wikifeat.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Idioma cambiado: {value}',
        TKey.AVAILABLE_LANGS: 'Idiomas disponibles: {values}',
    },

    'it': {
        TKey.START_COMMANDS: (
            "Comandi disponibili:\n"
            "/status — controlla stato\n"
            "/random — articolo casuale\n"
            "/limit — limite rimanente\n"
            "/lang — scegli lingua (choose language)\n"
            "/info — info"
        ),
        TKey.SPAM_BLOCK: 'Troppe richieste.',
        TKey.LIMIT_REMAINING: 'Richieste rimanenti: {count}',
        TKey.LIMIT_EXHAUSTED: 'Limite giornaliero raggiunto.',
        TKey.NEED_SUBSCRIPTION: 'Iscriviti a @wikifeat.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Lingua cambiata: {value}',
        TKey.AVAILABLE_LANGS: 'Lingue disponibili: {values}',
    },

    'pt': {
        TKey.START_COMMANDS: (
            "Comandos disponíveis:\n"
            "/status — verificar status\n"
            "/random — artigo aleatório\n"
            "/limit — limite restante\n"
            "/lang — escolher idioma (choose language)\n"
            "/info — info"
        ),
        TKey.SPAM_BLOCK: 'Muitas solicitações.',
        TKey.LIMIT_REMAINING: 'Solicitações restantes: {count}',
        TKey.LIMIT_EXHAUSTED: 'Limite diário atingido.',
        TKey.NEED_SUBSCRIPTION: 'Inscreva-se em @wikifeat.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Idioma alterado: {value}',
        TKey.AVAILABLE_LANGS: 'Idiomas disponíveis: {values}',
    },

    'pl': {
        TKey.START_COMMANDS: (
            "Dostępne komendy:\n"
            "/status — sprawdź status\n"
            "/random — losowy artykuł\n"
            "/limit — pozostały limit\n"
            "/lang — wybierz język (choose language)\n"
            "/info — info"
        ),
        TKey.SPAM_BLOCK: 'Zbyt wiele запросów.',
        TKey.LIMIT_REMAINING: 'Pozostałe запросы: {count}',
        TKey.LIMIT_EXHAUSTED: 'Limit dzienny wyczerpany.',
        TKey.NEED_SUBSCRIPTION: 'Zasubskrybuj @wikifeat.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Język zmieniony: {value}',
        TKey.AVAILABLE_LANGS: 'Dostępne języki: {values}',
    },

    'be': {
        TKey.START_COMMANDS: (
            "Даступныя каманды:\n"
            "/status — праверыць статус\n"
            "/random — выпадковы артыкул\n"
            "/limit — астатні ліміт\n"
            "/lang — выбраць мову (choose language)\n"
            "/info — інфармацыя"
        ),
        TKey.SPAM_BLOCK: 'Занадта частыя запыты.',
        TKey.LIMIT_REMAINING: 'Засталося запытаў: {count}',
        TKey.LIMIT_EXHAUSTED: 'Сутачны ліміт вычарпаны.',
        TKey.NEED_SUBSCRIPTION: 'Падпішыцеся на @wikifeat.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Мова зменена: {value}',
        TKey.AVAILABLE_LANGS: 'Даступныя мовы: {values}',
    },

    'kk': {
        TKey.START_COMMANDS: (
            "Қолжетімді командалар:\n"
            "/status — күйді тексеру\n"
            "/random — кездейсоқ мақала\n"
            "/limit — қалған лимит\n"
            "/lang — тілді таңдау (choose language)\n"
            "/info — ақпарат"
        ),
        TKey.SPAM_BLOCK: 'Өте жиі сұраулар.',
        TKey.LIMIT_REMAINING: 'Қалған сұраулар: {count}',
        TKey.LIMIT_EXHAUSTED: 'Күндік лимит аяқталды.',
        TKey.NEED_SUBSCRIPTION: '@wikifeat арнасына жазылыңыз.',
        TKey.STATUS_OK: 'ok',
        TKey.LANG_CHANGED: 'Тіл өзгертілді: {value}',
        TKey.AVAILABLE_LANGS: 'Қолжетімді тілдер: {values}',
    },
}

for lang, data in BOT_TRANSLATIONS.items():
    TRANSLATIONS.setdefault(lang, {}).update(data)

def translate(lang: str, key: TKey, **kwargs) -> str:
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    template = lang_dict.get(key, key.value)
    return template.format(**kwargs)
