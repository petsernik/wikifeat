from telegram import InputMediaPhoto, InputMediaAnimation

from bot.keyboards.disambig import build_disambig_keyboard
from bot.services.disambig import get_session, get_disambig_keyboard_from_session
from config import SELF_MADE_IMAGE_CASE, get_config
from db import update_image_desc
from models import DisambigLevel
from parse import get_caption, get_article
from utils import get_img_buf_by_text


async def render_article(
        context,
        chat_id,
        lang,
        query,
        *,
        keyboard=None,
        ctx_req=None,
        page=0,
        edit_message=None,
):
    cfg = await get_config(chat_id, query, lang)

    article, ctx = await get_article(cfg, ctx_req=ctx_req)

    if not article:
        if edit_message:
            if edit_message.photo or edit_message.animation or edit_message.video:
                await edit_message.edit_caption("Error")
            else:
                await edit_message.edit_text("Error")
        else:
            await context.bot.send_message(chat_id, "Error")
        return

    # =========================
    # MEDIA
    # =========================
    media, media_is_animation = None, False

    if article.image:
        if article.image.desc == SELF_MADE_IMAGE_CASE:
            media = get_img_buf_by_text(article.title)
        else:
            media = article.image.desc
            media_is_animation = article.image.is_animation

    # =========================
    # CAPTION
    # =========================
    if article.is_disambig:
        caption = get_caption(
            article,
            cfg.RULES_URL,
            ctx,
            use_only_first_paragraph=True
        )
    else:
        caption = get_caption(article, cfg.RULES_URL, ctx)

    file_id = None

    # =========================
    # DISAMBIG SESSION UPDATE
    # =========================

    if article.is_disambig:
        if edit_message:
            session = get_session(context, edit_message.message_id)

            session.push(
                DisambigLevel(
                    titles=article.disambig_titles,
                    caption=caption,
                    media=media,
                    media_is_animation=media_is_animation,
                )
            )

            keyboard = get_disambig_keyboard_from_session(session)

        if not edit_message:
            keyboard = build_disambig_keyboard(
                article.disambig_titles,
                0
            )
    else:
        keyboard = keyboard
    # =========================
    # EDIT EXISTING MESSAGE
    # =========================
    if edit_message:

        if media:

            if media_is_animation:
                media_obj = InputMediaAnimation(
                    media=media,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                media_obj = InputMediaPhoto(
                    media=media,
                    caption=caption,
                    parse_mode="HTML"
                )

            result = await edit_message.edit_media(
                media=media_obj,
                reply_markup=keyboard
            )

            if isinstance(result, type(edit_message)):

                if result.animation:
                    file_id = result.animation.file_id
                elif result.photo:
                    file_id = result.photo[-1].file_id

            if not file_id:
                file_id = media

        else:

            if edit_message.photo or edit_message.animation or edit_message.video:
                await edit_message.edit_caption(
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                await edit_message.edit_text(
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

        msg = edit_message

    # =========================
    # SEND NEW MESSAGE
    # =========================
    else:

        if media:

            if media_is_animation:

                msg = await context.bot.send_animation(
                    chat_id,
                    animation=media,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

                file_id = msg.animation.file_id

            else:

                msg = await context.bot.send_photo(
                    chat_id,
                    photo=media,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

                file_id = msg.photo[-1].file_id

        else:
            msg = await context.bot.send_message(
                chat_id,
                caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )

    # =========================
    # CACHE UPDATE
    # =========================
    if media and article.image and article.image.desc != file_id:
        article.image.desc = file_id
        if article.is_disambig and edit_message:
            session = get_session(context, msg.message_id)
            session.current().media = file_id
        await update_image_desc(article.link, file_id)

    # =========================
    # DISAMBIG STATE
    # =========================
    if article.is_disambig and not edit_message:
        session = get_session(context, msg.message_id)

        session.push(
            DisambigLevel(
                titles=article.disambig_titles,
                caption=caption,
                media=file_id,
                media_is_animation=media_is_animation,
            )
        )


async def edit(update, context, article, caption, keyboard, media=None, media_is_animation=False):
    msg = update.callback_query.message

    # =========================
    # MEDIA LOGIC (КАК В send)
    # =========================
    if media:
        if media_is_animation:
            media_obj = InputMediaAnimation(
                media=media,
                caption=caption,
                parse_mode="HTML"
            )
        else:
            media_obj = InputMediaPhoto(
                media=media,
                caption=caption,
                parse_mode="HTML"
            )

        await msg.edit_media(
            media=media_obj,
            reply_markup=keyboard
        )
    else:
        await msg.edit_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )


async def notify(update, text):
    if update.callback_query:
        await update.callback_query.answer(
            text=text or "",
            show_alert=bool(text)
        )
    elif text:
        await update.effective_message.reply_text(text)
