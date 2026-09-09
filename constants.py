import os

# ==== TELEGRAM ====
TELEGRAM_BOT_TOKEN = os.getenv('WIKIFEATTOKEN')
TELEGRAM_BOT_TEST_TOKEN = os.getenv('WIKIFEATTESTTOKEN')
TELEGRAM_PROXY = os.getenv('TELEGRAM_PROXY')
OWNER_ID = int(os.getenv('TELEGRAM_ID_OWNER', '0'))

CHANNEL_USERNAME = '@wikifeat'
USER_AGENT = 'wikifeat/0.55 (https://github.com/petsernik/wikifeat)'

# ==== BOT ====
ENSURE_BOT_RUNNING = os.getenv('WIKIFEATENSUREBOTRUNNING')

WATCHDOG_SLEEP_TIME = 45.0
RESTART_COOLDOWN = 90.0
DEAD_TIMEOUT = 45.0
BOT_PROCESS_NAME = 'wikifeatbotprocess'

# ==== PATHS ====
DIR_PATH = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(DIR_PATH, 'Renju.otf')
INIT_SQL_PATH = os.path.join(DIR_PATH, 'schema.sql')

# ==== IMAGE CASES ====
NAZI_IMAGE_CASE = (
    'I condemn nazi ideology. '
    'If this appears in an exception, generate the image manually for this case.'
)

SELF_MADE_IMAGE_CASE = (
    'If this appears in an exception, generate the image manually for this case.'
)

# ==== PAGINATION ====
PAGE_SIZE = 8

# ==== LIMITS ====
DAILY_TOTAL_LIMIT = 4900
DAILY_USER_LIMIT = 100

# ==== SPAM ====
SPAM_INTERVAL = 0.1

# ==== COMMANDS ====
CMD_STATUS = 'status'
CMD_RANDOM = 'random'
CMD_GET = 'get'
CMD_CANCEL = 'cancel'
CMD_LIMIT = 'limit'
CMD_LANG = 'lang'
CMD_ABOUT = 'about'
CMD_UPDATE = 'update'

# ==== POSTGRES PARAMETERS ====
DB_USER = os.getenv('WIKIFEAT_DB_USER', 'postgres')
DB_PASSWORD = os.getenv('WIKIFEAT_DB_PASSWORD')
DB_NAME = os.getenv('WIKIFEAT_DB_NAME', 'wikifeat')
DB_TEST_NAME = os.getenv('WIKIFEAT_DB_TEST_NAME', 'wikifeattest')
DB_HOST = os.getenv('WIKIFEAT_DB_HOST', '127.0.0.1')
DB_MIN_SIZE = int(os.getenv('WIKIFEAT_DB_MIN_SIZE', '1'))
DB_MAX_SIZE = int(os.getenv('WIKIFEAT_DB_MAX_SIZE', '10'))
