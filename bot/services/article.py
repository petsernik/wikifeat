from telegram import Update
from telegram.ext import ContextTypes

from bot.services.access import check_and_increment_limit, check_access
from bot.services.render import render_article, notify
from config import get_config
from i18n import translate, TKey
from parse import get_ctx_req_by_config


async def handle_article(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        title: str,
        lang_val: str,
        uid: int,
        chat_id: int,
        check_limit: bool = True,
        keyboard=None,
        use_cache=True,
        edit_message=None,
        page=0,
):
    notify_text = None

    try:
        if not title:
            notify_text = "bot error: empty title when handling article"
            return

        ok, reason = await check_access(context, update.effective_user.id)
        if not ok:
            notify_text = translate(lang_val, reason)
            return

        ctx_req = await get_ctx_req_by_config(
            await get_config(chat_id, title, lang_val),
            use_cache
        )

        # кеш → сразу отправляем без лимита
        if ctx_req.cached:
            await render_article(
                context,
                chat_id,
                lang_val,
                title,
                keyboard=keyboard,
                ctx_req=ctx_req,
                edit_message=edit_message,
                page=page,
            )
            return

        # лимит
        if check_limit:
            ok = await check_and_increment_limit(uid)

            if not ok:
                notify_text = translate(lang_val, TKey.LIMIT_EXCEEDED)
                return

        await render_article(
            context,
            chat_id,
            lang_val,
            title,
            keyboard=keyboard,
            ctx_req=ctx_req,
            edit_message=edit_message,
            page=page,
        )

    finally:
        await notify(update, notify_text)