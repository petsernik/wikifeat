import asyncio

from telegram import InlineKeyboardMarkup
from telegram.error import BadRequest, RetryAfter, TimedOut, NetworkError

from i18n import translate, TKey


async def processing_message_worker(
        update,
        lang_val,
        title,
        finished: asyncio.Event,
        finished_bad: asyncio.Event,
        keyboard: InlineKeyboardMarkup,
):
    try:
        try:
            await asyncio.wait_for(finished.wait(), timeout=5)

            if finished_bad.is_set():
                await update.effective_chat.send_message(
                    f'{translate(lang_val, TKey.PROCESSING_ERROR)} ({title})',
                    reply_markup=keyboard,
                )

            return

        except asyncio.TimeoutError:
            pass

        icons = ['⏳', '⌛']
        idx = 0

        msg = await update.effective_chat.send_message(
            f'{icons[idx]} {translate(lang_val, TKey.PROCESSING_REQUEST)}'
        )

        while True:
            try:
                await asyncio.wait_for(finished.wait(), timeout=5)
                break

            except asyncio.TimeoutError:
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
        else:
            try:
                await msg.delete()
            except BadRequest:
                pass

    except asyncio.CancelledError:
        pass

    except RetryAfter as e:
        print(f"RetryAfter in processing_message_worker: {e}")

    except (TimedOut, NetworkError) as e:
        print(f"Telegram network error in processing_message_worker: {e}")

    except Exception as e:
        print(f"Unexpected error in processing_message_worker: {e}")
