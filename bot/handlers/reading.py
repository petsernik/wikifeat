from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.registry import callback
from bot.services.article import handle_article


@callback("^reading\\|")
async def reading_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    data = query.data.split("|")

    # reading|page_info
    if data[1] == "page_info":
        return

    # reading|start|lang|title
    if data[1] == "start":
        lang = data[2]
        title = data[3]

        page = 0

        await handle_article(
            update=update,
            context=context,
            title=title,
            lang_val=lang,
            uid=query.from_user.id,
            chat_id=query.message.chat.id,
            page=page,
            reading=True,
        )

        return

    # reading|back|lang|title
    if data[1] == "back":
        msg = update.effective_message

        if msg:
            await msg.delete()

        return

    # reading|<page>|lang|title
    page = int(data[1])
    lang = data[2]
    title = data[3]

    await handle_article(
        update=update,
        context=context,
        title=title,
        lang_val=lang,
        uid=query.from_user.id,
        chat_id=query.message.chat.id,
        edit_message=query.message,
        page=page,
        reading=True,
    )
