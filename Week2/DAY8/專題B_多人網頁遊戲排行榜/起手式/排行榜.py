# 專題 B 起手式：排行榜服務（能跑的最小骨架）
#
# 這是一個「獨立」的排行榜微服務，先讓它自己能跑通，之後再把它併進 web_shooter：
#   - POST /api/score   body: {"name": "小明", "kills": 7}   → 存一筆成績
#   - GET  /api/leaderboard                                   → 回擊殺數前 10 名 JSON
#   - GET  /                                                  → 排行榜網頁（可手動送測試分數）
#
# 併進 web_shooter 的方法（README 有寫）：
#   把「初始化資料庫 / 記錄成績 / leaderboard 路由」這三塊，
#   複製到 web_shooter/server.py，在玩家陣亡時呼叫 記錄成績()。
#
# 重點：分數一定要在 SERVER 端寫（擊殺數是 server 權威狀態），不要相信瀏覽器傳來的分數。

import sqlite3
from pathlib import Path

from aiohttp import web

BASE = Path(__file__).parent
DB_PATH = BASE / "leaderboard.db"


# ====== 資料庫層 ======
def 初始化資料庫():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS 成績 (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               kills INTEGER NOT NULL,
               created_at TEXT DEFAULT CURRENT_TIMESTAMP
           )"""
    )
    conn.commit()
    conn.close()


def 記錄成績(name, kills):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO 成績 (name, kills) VALUES (?, ?)", (name, int(kills)))
    conn.commit()
    conn.close()


def 前十名():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT name, MAX(kills) AS best FROM 成績 GROUP BY name ORDER BY best DESC LIMIT 10"
    )
    資料 = [{"name": r[0], "kills": r[1]} for r in cur.fetchall()]
    conn.close()
    return 資料


# ====== 路由 ======
async def 首頁(request):
    return web.FileResponse(BASE / "leaderboard.html")


async def 送出成績(request):
    try:
        data = await request.json()
        name = str(data["name"]).strip() or "匿名"
        kills = int(data["kills"])
    except Exception:
        return web.json_response({"error": "需要 {name, kills}"}, status=400)
    記錄成績(name, kills)
    return web.json_response({"ok": True})


async def 取排行榜(request):
    return web.json_response(前十名())


def build_app():
    初始化資料庫()
    app = web.Application()
    app.router.add_get("/", 首頁)
    app.router.add_post("/api/score", 送出成績)
    app.router.add_get("/api/leaderboard", 取排行榜)
    return app


if __name__ == "__main__":
    print("排行榜服務開啟於 http://localhost:8770/")
    web.run_app(build_app(), host="0.0.0.0", port=8770)
