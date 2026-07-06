-- ============================================================
-- 電商購物網站 — PostgreSQL 資料表建立語法
-- ============================================================
-- 使用方式：
--   1. 登入 PostgreSQL
--   2. 建立資料庫（例如 CREATE DATABASE ecommerce;）
--   3. 執行此 SQL 檔案：\i schema.sql
-- ============================================================

-- 使用者表（買方 / 商家）
CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    password   TEXT NOT NULL,
    role       TEXT NOT NULL CHECK (role IN ('buyer', 'seller')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引：加速登入時的 username 查詢
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

-- 商品表
CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    price       NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    description TEXT DEFAULT '',
    image_url   TEXT DEFAULT '',
    seller_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 購物車表
CREATE TABLE IF NOT EXISTS cart_items (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity   INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, product_id)
);
