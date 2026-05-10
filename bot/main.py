from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot.handlers.admin import reborn, release
from bot.handlers.callbacks import lang_select, more_random, disambig_page, disambig_open, disambig_nav, disambig_back, \
    disambig_back_nav, noop
from bot.handlers.commands import start, about, status, limit, cmd_lang, random, get_cmd, cancel, update_cmd
from bot.handlers.text import handle_text
from config import (
    TELEGRAM_BOT_TOKEN, CMD_STATUS, CMD_RANDOM, CMD_LIMIT, CMD_LANG, CMD_ABOUT,
    CMD_GET, CMD_CANCEL, CMD_UPDATE
)
from db import init_db, close_db, get_lang, set_lang, has_featured_articles, update_featured_articles_in_db
from i18n import TRANSLATIONS
from parsers import fetch_featured_titles
from utils import normalize_lang




def register_handlers(app):
    # =========================
    # commands
    # =========================
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(CMD_ABOUT, about))
    app.add_handler(CommandHandler(CMD_STATUS, status))
    app.add_handler(CommandHandler(CMD_LIMIT, limit))
    app.add_handler(CommandHandler(CMD_LANG, cmd_lang))
    app.add_handler(CommandHandler(CMD_RANDOM, random))
    app.add_handler(CommandHandler(CMD_GET, get_cmd))
    app.add_handler(CommandHandler(CMD_CANCEL, cancel))
    app.add_handler(CommandHandler(CMD_UPDATE, update_cmd))
    app.add_handler(CommandHandler("reborn", reborn))
    app.add_handler(CommandHandler("release", release))

    # callbacks
    app.add_handler(CallbackQueryHandler(lang_select, pattern="^lang:"))
    app.add_handler(CallbackQueryHandler(more_random, pattern="^more_random$"))
    app.add_handler(CallbackQueryHandler(disambig_page, pattern="^page\\|"))
    app.add_handler(CallbackQueryHandler(disambig_open, pattern="^open\\|"))
    app.add_handler(CallbackQueryHandler(disambig_nav, pattern="^nav\\|"))
    app.add_handler(CallbackQueryHandler(disambig_back, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(disambig_back_nav, pattern="^back_nav$"))
    app.add_handler(CallbackQueryHandler(noop, pattern="^noop$"))

    # text router
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # =========================
    # DB INIT
    # =========================
    async def post_init(_: Application):
        await init_db()
        for lang in TRANSLATIONS.keys():
            try:
                if await has_featured_articles(lang):
                    continue

                titles = await fetch_featured_titles(lang)

                if not titles:
                    continue

                await update_featured_articles_in_db(lang, titles)

            except Exception as exc:
                print(f"[featured init error] lang={lang}: {exc}")

    async def post_shutdown(_: Application):
        await close_db()

    app.post_init = post_init
    app.post_shutdown = post_shutdown

    register_handlers(app)

    # =========================
    # RUN
    # =========================
    app.run_polling()


# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    main()
