import json
import logging
from datetime import datetime
from typing import Optional, Tuple

import asyncpg

from config import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_MIN_SIZE,
    DB_MAX_SIZE,
    INIT_SQL_PATH
)
from models import Article
from utils import get_quote_url_by_str

pool: asyncpg.Pool | None = None


async def init_db(db_name: str):
    """
    Инициализация подключения к PostgreSQL и загрузка схемы.
    """

    global pool
    if pool:
        return

    pool = await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        database=db_name,
        host=DB_HOST,
        min_size=DB_MIN_SIZE,
        max_size=DB_MAX_SIZE
    )

    logging.info("Database pool created")

    # загрузка схемы
    async with pool.acquire() as conn:
        with open(INIT_SQL_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        try:
            await conn.execute(schema_sql)
            logging.info("Database schema initialized")
        except Exception as e:
            logging.exception("Failed to initialize schema: %s", e)
            raise


def get_pool() -> asyncpg.Pool:
    """
    Получение глобального пула соединений.
    """
    if pool is None:
        raise RuntimeError("Database is not initialized. Call init_db() first.")
    return pool


pool_backup: asyncpg.Pool | None = None


async def get_backup_pool() -> asyncpg.Pool:
    global pool_backup

    if pool_backup is None:
        pool_backup = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            database="wikifeatbackup",
            host=DB_HOST,
            min_size=DB_MIN_SIZE,
            max_size=DB_MAX_SIZE,
        )

    return pool_backup


async def close_db():
    """
    Корректное закрытие пула (важно при shutdown бота).
    """
    global pool

    if pool:
        await pool.close()
        pool = None
        logging.info("Database pool closed")


async def get_random_featured_title(lang: str) -> Optional[str]:
    if not pool:
        return None

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT title
            FROM featured_articles
            WHERE lang = $1
            ORDER BY RANDOM()
            LIMIT 1
            """,
            lang
        )

    return row["title"] if row else None


async def clear_all_featured_articles_in_db(lang: str):
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM featured_articles WHERE lang = $1",
                lang
            )


async def update_featured_articles_in_db(lang: str, titles: set[str]):
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO featured_articles (lang, title)
                VALUES ($1, $2)
                ON CONFLICT (lang, title) DO NOTHING
                """,
                [(lang, t) for t in titles]
            )


async def has_featured_articles(lang: str) -> bool:
    query = """
        SELECT EXISTS(
            SELECT 1 FROM featured_articles WHERE lang = $1
        )
    """
    return await pool.fetchval(query, lang)


# =========================
# LAST FEATURED ARTICLE (по языку)
# =========================

async def get_last_article(lang: str) -> str:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT title FROM last_featured_articles WHERE lang=$1",
            lang
        )
        return row["title"] if row else ''


async def set_last_article(lang: str, title: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO last_featured_articles(lang, title, date)
            VALUES($1, $2, CURRENT_DATE)
            ON CONFLICT (lang)
            DO UPDATE SET
                title = EXCLUDED.title,
                date = EXCLUDED.date
            """,
            lang, title
        )


# =========================
# LANG (пользователь)
# =========================

async def get_lang(user_id: int) -> str | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT lang FROM users WHERE user_id=$1",
            user_id
        )
        return row["lang"] if row else None


async def set_lang(user_id: int, lang: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users(user_id, lang)
            VALUES($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET lang = EXCLUDED.lang
            """,
            user_id, lang
        )


# =========================
# LIMITS
# =========================

async def increment_user_limit(user_id: int):
    async with pool.acquire() as conn:
        # пользовательский лимит
        await conn.execute(
            """
            INSERT INTO user_limits(user_id, date, count)
            VALUES($1, CURRENT_DATE, 1)
            ON CONFLICT (user_id, date)
            DO UPDATE SET count = user_limits.count + 1
            """,
            user_id
        )

        # глобальный лимит
        await conn.execute(
            """
            INSERT INTO global_limits(date, total)
            VALUES(CURRENT_DATE, 1)
            ON CONFLICT (date)
            DO UPDATE SET total = global_limits.total + 1
            """
        )


async def get_user_limit(user_id: int) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT count FROM user_limits
            WHERE user_id=$1 AND date=CURRENT_DATE
            """,
            user_id
        )
        return row["count"] if row else 0


async def get_global_limit() -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT total FROM global_limits
            WHERE date=CURRENT_DATE
            """
        )
        return row["total"] if row else 0


async def reset_user_limit(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM user_limits
            WHERE user_id=$1 AND date=CURRENT_DATE
            """,
            user_id
        )


# =========================
# ARTICLE CACHE
# =========================
async def save_article_to_db(article: Article) -> None:
    data = article.to_db()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO articles_cache (
                title,
                paragraphs,
                link,
                image,
                is_disambig,
                disambig_titles
            )
            VALUES ($1, $2::jsonb, $3, $4::jsonb, $5, $6::jsonb)
            ON CONFLICT (link) DO UPDATE
            SET
                title = EXCLUDED.title,
                paragraphs = EXCLUDED.paragraphs,
                image = EXCLUDED.image,
                is_disambig = EXCLUDED.is_disambig,
                disambig_titles = EXCLUDED.disambig_titles,
                updated_at = NOW()
            """,
            data["title"],
            data["paragraphs"],
            data["link"],
            data["image"],
            data["is_disambig"],
            data["disambig_titles"],
        )


async def update_image_desc(article_link: str, file_id: str):
    query = """
        UPDATE articles_cache
        SET image = jsonb_set(image, '{desc}', to_jsonb($2::text))
        WHERE link = $1
    """
    await pool.execute(query, article_link, file_id)


async def get_article_from_db(link: str, with_image: bool) -> Optional[Article]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM articles_cache
            WHERE link = $1
        """, link)

    if not row:
        return None

    return Article.from_db(row, with_image)


async def article_cached(link: str) -> bool:
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            SELECT 1 FROM articles_cache
            WHERE link = $1
        """, link) is not None


async def get_article_with_meta(link: str, with_image: bool) -> Optional[Tuple[Article, datetime, datetime]]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM articles_cache
            WHERE link = $1
        """, link)

    if not row:
        return None

    article = Article.from_db(row, with_image)
    created_at = row["created_at"]
    updated_at = row["updated_at"]

    return article, created_at, updated_at


async def is_article_stale(link: str, max_age_minutes: int) -> bool:
    async with pool.acquire() as conn:
        result = await conn.fetchval("""
            SELECT
                created_at < NOW() - ($2 * INTERVAL '1 minute')
            FROM articles_cache
            WHERE link = $1
        """, link, max_age_minutes)

    # если статьи нет → считаем устаревшей
    return result is None or result


# =========================
# REDIRECTS CACHE
# =========================
async def get_cached_final_url(url_start: str) -> Optional[str]:
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            SELECT url_final
            FROM quote_url_cache
            WHERE url_start = $1
        """, url_start)


async def set_cached_final_url(url_start: str, url_final: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO quote_url_cache (url_start, url_final)
            VALUES ($1, $2)
            ON CONFLICT (url_start) DO UPDATE
            SET url_final = EXCLUDED.url_final
        """, url_start, url_final)


# =========================
# MEDIAWIKI CACHE
# =========================
async def get_skip_prefixes_from_db(lang: str) -> Optional[Tuple[str, ...]]:
    row = await pool.fetchrow(
        """
        SELECT prefixes
        FROM skip_prefixes
        WHERE lang = $1
          AND updated_at > NOW() - INTERVAL '7 days'
        """,
        lang
    )
    if not row:
        return None

    return tuple(json.loads(row["prefixes"]))


async def save_skip_prefixes_to_db(lang: str, prefixes: Tuple[str, ...]):
    await pool.execute(
        """
        INSERT INTO skip_prefixes (lang, prefixes, updated_at)
        VALUES ($1, $2, NOW())
        ON CONFLICT (lang)
        DO UPDATE SET prefixes = EXCLUDED.prefixes,
                      updated_at = NOW()
        """,
        lang,
        json.dumps(prefixes),
    )


async def delete_url(lang: str, url_or_name: str):
    async with pool.acquire() as conn:
        async with conn.transaction():
            # нормализуем URL
            url = get_quote_url_by_str(lang, url_or_name)

            # -------------------------
            # 1. articles_cache
            # -------------------------
            row = await conn.fetchrow(
                """
                DELETE FROM articles_cache
                WHERE link = $1
                RETURNING title
                """,
                url
            )

            title = row["title"] if row else None

            # -------------------------
            # 2. quote_url_cache
            # -------------------------
            await conn.execute(
                """
                DELETE FROM quote_url_cache
                WHERE url_start = $1 OR url_final = $1
                """,
                url
            )

            # -------------------------
            # 3. featured_articles
            # -------------------------
            if title:
                await conn.execute(
                    """
                    DELETE FROM featured_articles
                    WHERE lang = $1 AND title = $2
                    """,
                    lang,
                    title
                )

                # -------------------------
                # 4. last_featured_articles
                # -------------------------
                await conn.execute(
                    """
                    DELETE FROM last_featured_articles
                    WHERE lang = $1 AND title = $2
                    """,
                    lang,
                    title
                )


async def insert_from_backup(table: str, conflict_columns: list[str]):
    backup_pool = await get_backup_pool()

    async with pool.acquire() as dst_conn, \
            backup_pool.acquire() as src_conn:

        # --- destination schema ONLY ---
        dst_columns = await dst_conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = $1
            ORDER BY ordinal_position
        """, table)

        columns = []
        for c in dst_columns:
            name = c["column_name"]

            if name == "id":
                continue

            columns.append(name)

        cols_sql = ", ".join(f'"{c}"' for c in columns)

        rows = await src_conn.fetch(
            f'SELECT {cols_sql} FROM "{table}"'
        )

        if not rows:
            return 0

        conflict_sql = ", ".join(f'"{c}"' for c in conflict_columns)

        placeholders = ", ".join(
            f"${i}"
            for i in range(1, len(columns) + 1)
        )

        query = f"""
            INSERT INTO "{table}" ({cols_sql})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_sql}) DO NOTHING
        """

        values = [
            tuple(row[col] for col in columns)
            for row in rows
        ]

        await dst_conn.executemany(query, values)

        # Если сбился счётчик:
        #
        # Явно вычисляем имя последовательности на основе переданного имени таблицы
        # seq_name = f"{table}_id_seq"
        #
        # # Обновляем счетчик в базе данных
        # await dst_conn.execute(f"""
        #             SELECT setval('{seq_name}', COALESCE(MAX(id), 1)) FROM "{table}";
        #         """)

        return len(values)
