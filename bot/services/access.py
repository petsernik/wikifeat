import time

from telegram.ext import ContextTypes

from constants import SPAM_INTERVAL, DAILY_TOTAL_LIMIT, DAILY_USER_LIMIT, CHANNEL_USERNAME
from db import get_pool
from i18n import TKey

user_last_request_time = {}


def is_spam(user_id: int) -> bool:
    now = time.time()
    last = user_last_request_time.get(user_id, 0)

    if now - last < SPAM_INTERVAL:
        return True

    user_last_request_time[user_id] = now
    return False


async def check_and_increment_limit(user_id: int) -> bool:
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():

            # --- global limit ---
            total_row = await conn.fetchrow(
                "SELECT total FROM global_limits WHERE date = CURRENT_DATE"
            )
            total = total_row["total"] if total_row else 0

            if total >= DAILY_TOTAL_LIMIT:
                return False

            # --- user limit ---
            user_row = await conn.fetchrow(
                """
                SELECT count FROM user_limits
                WHERE user_id=$1 AND date=CURRENT_DATE
                """,
                user_id
            )
            user_count = user_row["count"] if user_row else 0

            if user_count >= DAILY_USER_LIMIT:
                return False

            # --- increment user ---
            await conn.execute(
                """
                INSERT INTO user_limits(user_id, date, count)
                VALUES($1, CURRENT_DATE, 1)
                ON CONFLICT (user_id, date)
                DO UPDATE SET count = user_limits.count + 1
                """,
                user_id
            )

            # --- increment global ---
            await conn.execute(
                """
                INSERT INTO global_limits(date, total)
                VALUES(CURRENT_DATE, 1)
                ON CONFLICT (date)
                DO UPDATE SET total = global_limits.total + 1
                """
            )

            return True


async def is_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    m = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
    return m.status in ("member", "administrator", "creator")


async def check_access(context, user_id: int, decrease=False):
    if is_spam(user_id):
        return False, TKey.SPAM_BLOCK

    if not await is_subscribed(context, user_id):
        return False, TKey.NEED_SUBSCRIPTION

    if decrease:
        if not await check_and_increment_limit(user_id):
            return False, TKey.LIMIT_EXCEEDED

    return True, TKey.STATUS_OK
