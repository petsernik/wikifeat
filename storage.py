import json
import os

from config import LIMIT_FILE, TMP_FOLDER_PATH


def check_tmp_folder_exists():
    os.makedirs(TMP_FOLDER_PATH, exist_ok=True)


# =========================
# LAST ARTICLE
# =========================

def read_last_article(last_article_file: str) -> str:
    if not os.path.exists(last_article_file):
        return ''
    with open(last_article_file, 'r', encoding='utf-8') as file:
        return file.read().strip()


def write_last_article(title: str, last_article_file: str):
    with open(last_article_file, 'w', encoding='utf-8') as file:
        file.write(title)


# =========================
# LANG
# =========================
LANG_FILE = os.path.join(TMP_FOLDER_PATH, "user_lang.json")


def load_langs():
    if not os.path.exists(LANG_FILE):
        return {}
    try:
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_langs(data):
    tmp = LANG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, LANG_FILE)


# =========================
# LIMIT
# =========================
def load_limit():
    if not os.path.exists(LIMIT_FILE):
        return {"date": None, "total": 0, "users": {}}

    try:
        with open(LIMIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"date": None, "total": 0, "users": {}}


def save_limit(data):
    tmp = LIMIT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, LIMIT_FILE)
