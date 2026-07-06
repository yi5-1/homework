# 教學重點：aiohttp 後端 + PostgreSQL + 環境變數
#
#   瀏覽器 (HTML+JS)  <--HTTP-->  aiohttp (Python)  <--asyncpg-->  PostgreSQL
#      前端                          後端                            資料庫
#
# 只有兩個 API：
#   POST /api/register   → 註冊
#   POST /api/login      → 登入驗證（不保留 session，只回成功/失敗）

import os
from pathlib import Path

from aiohttp import web
import asyncpg
from dotenv import load_dotenv

BASE = Path(__file__).parent

# ====== 讀 .env（密碼從環境變數來，不寫死在程式碼裡）======
load_dotenv(BASE / ".env")

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "STUST2026AI"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}
SERVER_PORT = int(os.getenv("SERVER_PORT", 8001))

# 連線池：aiohttp 是 async，用 pool 才不會每次連線都重新握手
pool: asyncpg.Pool | None = None


# ====== 資料庫初始化 ======
async def 建立資料表():
    """程式啟動時建 users 表，已存在就不動"""
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         SERIAL PRIMARY KEY,
                username   TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# ====== HTTP handlers ======
async def 首頁(request):
    return web.FileResponse(BASE / "static" / "index.html")


async def api_註冊(request):
    """
    POST /api/register  body: {"username": "...", "password": "..."}
    """
    data = await request.json()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return web.json_response({"ok": False, "error": "帳號和密碼不能空白"}, status=400)
    if len(username) > 20 or len(password) > 50:
        return web.json_response({"ok": False, "error": "帳號≤20字、密碼≤50字"}, status=400)

    async with pool.acquire() as conn:
        try:
            # PostgreSQL 用 $1、$2 當佔位符（跟 SQLite 的 ? 不同）
            await conn.execute(
                "INSERT INTO users (username, password) VALUES ($1, $2)",
                username, password,
            )
        except asyncpg.UniqueViolationError:
            return web.json_response({"ok": False, "error": "此帳號已被註冊"}, status=400)

    return web.json_response({"ok": True, "message": f"註冊成功，歡迎 {username}"})


async def api_登入(request):
    """
    POST /api/login  body: {"username": "...", "password": "..."}
    只驗證帳密，不保留 session。
    """
    data = await request.json()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return web.json_response({"ok": False, "error": "請輸入帳號和密碼"}, status=400)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT password FROM users WHERE username=$1",
            username,
        )

    # 教學版：密碼明文比對。實務上要用 hash（例如 bcrypt / hashlib.pbkdf2_hmac）
    if row and row["password"] == password:
        return web.json_response({"ok": True, "message": f"登入成功，歡迎回來 {username}"})
    return web.json_response({"ok": False, "error": "帳號或密碼錯誤"}, status=401)


# ====== 生命週期 ======
async def on_startup(app):
    global pool
    try:
        pool = await asyncpg.create_pool(**DB_CONFIG, min_size=1, max_size=5)
    except Exception as e:
        print(f"[錯誤] 連不上 PostgreSQL：{e}")
        print(f"       設定：host={DB_CONFIG['host']} port={DB_CONFIG['port']} db={DB_CONFIG['database']} user={DB_CONFIG['user']}")
        raise
    await 建立資料表()
    print(f"已連上 PostgreSQL {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")


async def on_cleanup(app):
    if pool:
        await pool.close()


def main():
    app = web.Application()
    app.router.add_get("/",              首頁)
    app.router.add_post("/api/register", api_註冊)
    app.router.add_post("/api/login",    api_登入)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    print(f"Server 開啟於 http://127.0.0.1:{SERVER_PORT}/  (Ctrl+C 停止)")
    web.run_app(app, host="0.0.0.0", port=SERVER_PORT)


if __name__ == "__main__":
    main()
