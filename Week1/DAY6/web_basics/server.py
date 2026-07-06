# 教學重點：Web 三層架構（前端 / 後端 / 資料庫）
#
#   瀏覽器 (HTML+JS)  <--HTTP-->  aiohttp (Python)  <--SQL-->  SQLite
#      前端                          後端                       資料庫
#
# 資料的流動：
#   1. 使用者在瀏覽器輸入訊息，按「送出」
#   2. 前端 JS 用 fetch() 送 POST 到 /api/messages
#   3. 後端 aiohttp 收到 → 寫入 SQLite
#   4. 前端 fetch GET /api/messages 拉回所有訊息 → 更新畫面

import sqlite3
from pathlib import Path
from aiohttp import web

BASE = Path(__file__).parent
DB_PATH = BASE / "messages.db"


# ====== 資料庫層 ======
def 初始化資料庫():
    """程式啟動時建表；如果表已經存在就不動"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT,
            text       TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def 讀取所有訊息():
    conn = sqlite3.connect(DB_PATH)
    # 用 ? 佔位符查詢，不要用字串拼接（防 SQL injection）
    rows = conn.execute(
        "SELECT name, text, created_at FROM messages ORDER BY id DESC LIMIT 30"
    ).fetchall()
    conn.close()
    # 把 tuple 轉成 dict，讓前端拿到有名字的欄位
    return [
        {"name": name, "text": text, "created_at": created_at}
        for name, text, created_at in rows
    ]


def 新增訊息(name, text):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO messages (name, text) VALUES (?, ?)",
        (name, text),
    )
    conn.commit()
    conn.close()


# ====== 後端層（HTTP routes）======
async def 首頁(request):
    """GET / → 回傳 index.html（純靜態頁面）"""
    return web.FileResponse(BASE / "static" / "index.html")


async def api_取得訊息(request):
    """GET /api/messages → 回傳目前所有訊息（JSON 格式）"""
    return web.json_response(讀取所有訊息())


async def api_新增訊息(request):
    """POST /api/messages → 從 body 讀 JSON，存進 DB"""
    data = await request.json()
    name = str(data.get("name", "")).strip()[:20] or "匿名"
    text = str(data.get("text", "")).strip()[:200]
    if not text:
        return web.json_response({"error": "訊息不可空白"}, status=400)
    新增訊息(name, text)
    return web.json_response({"ok": True})


# ====== 啟動 ======
def main():
    初始化資料庫()

    app = web.Application()
    # 網址 -> 對應的處理函式
    app.router.add_get("/",              首頁)
    app.router.add_get("/api/messages",  api_取得訊息)
    app.router.add_post("/api/messages", api_新增訊息)

    print("Server 開啟於 http://127.0.0.1:8000/  (Ctrl+C 停止)")
    web.run_app(app, host="0.0.0.0", port=8089)


if __name__ == "__main__":
    main()
