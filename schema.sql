-- =========================
-- USERS (настройки пользователя)
-- =========================
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    lang TEXT NOT NULL DEFAULT 'en'
);


-- =========================
-- LAST FEATURED ARTICLE
-- =========================
CREATE TABLE IF NOT EXISTS last_featured_articles (
    lang TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    date DATE NOT NULL
);


-- =========================
-- USER LIMITS (дневные лимиты)
-- =========================
CREATE TABLE IF NOT EXISTS user_limits (
    user_id BIGINT,
    date DATE,
    count INT NOT NULL DEFAULT 0,

    PRIMARY KEY (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);


-- =========================
-- GLOBAL LIMITS (по дате)
-- =========================
CREATE TABLE IF NOT EXISTS global_limits (
    date DATE PRIMARY KEY,
    total INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS featured_articles (
    id SERIAL PRIMARY KEY,
    lang TEXT NOT NULL,
    title TEXT NOT NULL,
    UNIQUE(lang, title)
);

CREATE TABLE IF NOT EXISTS articles_cache (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    paragraphs JSONB NOT NULL,
    link TEXT NOT NULL UNIQUE,
    image JSONB
);

ALTER TABLE articles_cache
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE articles_cache
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE TABLE IF NOT EXISTS quote_url_cache (
    url_start TEXT PRIMARY KEY,
    url_final TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skip_prefixes (
    lang TEXT PRIMARY KEY,
    prefixes TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL
);