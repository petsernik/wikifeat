from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.callbacks import get_user_lang
from bot.services.article import handle_article
from bot.state.user_state import STATE_GET, STATE_UPDATE, clear_state, get_state, STATE_NONE
from i18n import translate, TKey


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()

    state = get_state(uid)

    lang_val = await get_user_lang(uid, update.effective_user.language_code)

    if state in (STATE_GET, STATE_NONE, STATE_UPDATE):
        try:
            await handle_article(
                update,
                context,
                text,
                lang_val,
                uid,
                update.effective_chat.id,
                check_limit=True,
                use_cache=state != STATE_UPDATE,
            )
        except:
            await update.message.reply_text(translate(lang_val, TKey.GET_ERROR))
        finally:
            clear_state(uid)