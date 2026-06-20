import os

TELEGRAM_BOT_TOKEN = os.environ.get('WIKIFEATTOKEN')
TELEGRAM_BOT_TEST_TOKEN = os.environ.get('WIKIFEATTESTTOKEN')
TELEGRAM_PROXY = os.environ.get('TELEGRAM_PROXY')
OWNER_ID = int(os.getenv("TELEGRAM_ID_OWNER", "0"))

WATCHDOG_SLEEP_TIME = 45.0
RESTART_COOLDOWN = 90.0
DEAD_TIMEOUT = 45.0

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(DIR_PATH, "Renju.otf")
NAZI_IMAGE_CASE = \
    "I condemn nazi ideology. If this appears in an exception, generate the image manually for this case."
SELF_MADE_IMAGE_CASE = "If this appears in an exception, generate the image manually for this case."

CHANNEL_USERNAME = "@wikifeat"
User_Agent = 'wikifeat/0.55 (https://github.com/petsernik/wikifeat)'

PAGE_SIZE = 8

# ==== LIMITS ====
DAILY_TOTAL_LIMIT = 4900
DAILY_USER_LIMIT = 100

# ==== SPAM ====
SPAM_INTERVAL = 0.1

# ==== COMMANDS ====
CMD_STATUS = "status"
CMD_RANDOM = "random"
CMD_GET = "get"
CMD_CANCEL = "cancel"
CMD_LIMIT = "limit"
CMD_LANG = "lang"
CMD_ABOUT = "about"
CMD_UPDATE = "update"

# ==== POSTGRES PARAMETERS ====
DB_USER = 'postgres'
DB_PASSWORD = os.environ.get('POSTGRES_DB_PASSWORD')
DB_NAME = 'wikifeat'
DB_TEST_NAME = 'wikifeattest'
DB_HOST = '127.0.0.1'
DB_MIN_SIZE = 1
DB_MAX_SIZE = 10

INIT_SQL_PATH = os.path.join(DIR_PATH, 'schema.sql')
