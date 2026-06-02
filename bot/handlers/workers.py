import asyncio

from telegram import InlineKeyboardMarkup
from telegram.error import BadRequest

from i18n import translate, TKey


async def processing_message_worker(update, lang_val, title, finished_ok: asyncio.Event, finished_bad: asyncio.Event,
                                    keyboard: InlineKeyboardMarkup):
    try:
        await asyncio.sleep(5)

        if finished_bad.is_set():
            await update.effective_chat.send_message(
                f'{translate(lang_val, TKey.PROCESSING_ERROR)} ({title})',
                reply_markup=keyboard,
            )
            return
        elif finished_ok.is_set():
            return

        icons = ['⏳', '⌛']
        idx = 0

        msg = await update.effective_chat.send_message(
            f'{icons[idx]} {translate(lang_val, TKey.PROCESSING_REQUEST)}'
        )

        while not (finished_ok.is_set() or finished_bad.is_set()):
            await asyncio.sleep(5)

            idx = (idx + 1) % len(icons)

            try:
                await msg.edit_text(
                    f'{icons[idx]} {translate(lang_val, TKey.PROCESSING_REQUEST)}'
                )
            except BadRequest:
                pass

        if finished_bad.is_set():
            await msg.edit_text(
                f'{translate(lang_val, TKey.PROCESSING_ERROR)} ({title})',
                reply_markup=keyboard,
            )
        elif finished_ok.is_set():
            await msg.delete()

    except asyncio.CancelledError:
        pass
