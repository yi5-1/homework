# 專題 B — 多人網頁遊戲排行榜

拿 DAY6 已經能跑的 `web_shooter`（瀏覽器多人射擊）當底，加上「帳號 + 存分數 + 排行榜」，變成一個有記憶的線上遊戲。

**整合**：DAY6（WebSocket 遊戲 + 資料庫）＋ DAY5（多人架構觀念）＋ DAY2（分數 / 邏輯）
**難度** ★★★★ ｜ **建議 3–4 人**

---

## 系統架構

```
瀏覽器 Canvas  ──WebSocket──►  aiohttp server（遊戲 tick）
     ▲                              │
     │  排行榜頁 (fetch GET)         ├─► 遊戲結束時寫 (玩家, 擊殺數, 時間) 進 DB
     └──────────────────────────────┴─► /api/leaderboard 回傳前 10 名
```

遊戲本體 `web_shooter` 已經會跑，你的工作是把「一局結束的成績」記下來並排名。

---

## 必做功能

1. 讓 `web_shooter` 能正常跑（先照它的 README 跑起來）。
2. 玩家死亡 / 一局結束時，把「玩家 ID + 擊殺數（或存活時間）」寫進資料庫。
   - DB 二選一：SQLite（簡單，參考 `web_basics`）或 PostgreSQL（參考 `web_auth`）。
3. 新增 `/api/leaderboard`：回傳擊殺數前 10 名的 JSON。
4. 新增一個排行榜網頁：`fetch` 那個 API，用 HTML 表格列出前 10 名。

## 加分功能

- 帳號系統：借 `web_auth` 的註冊 / 登入，讓分數綁在帳號上、能累計。
- 排行榜用前端畫 bar chart（Canvas 或簡單 div 長條），或後端用 matplotlib 產圖回傳。
- 「本局結算畫面」：死亡後顯示這局擊殺數 + 目前排名。
- 每日榜 / 總榜切換。

---

## 從哪裡改起

| 你要的功能 | 抄這個檔 |
|---|---|
| 遊戲本體（別重寫）| `Week1/DAY6/web_shooter/`（整包直接用）|
| server 端加 API 路由 | `Week1/DAY6/web_shooter/server.py`（照既有 route 加 `/api/leaderboard`）|
| 寫 / 讀 SQLite | `Week1/DAY6/web_basics/server.py` |
| PostgreSQL 連線池 + `.env` | `Week1/DAY6/web_auth/server.py`、`.env.example` |
| 註冊 / 登入 | `Week1/DAY6/web_auth/` |
| 前端 fetch + 顯示 | `Week1/DAY6/web_basics/static/index.html` |

> **提醒**：分數要在 **server 端**算並寫 DB（擊殺數是 server 權威狀態），不要相信瀏覽器傳來的分數，否則會被作弊。這也是 DAY5 權威伺服器的觀念。

## 需要安裝
```bash
pip install aiohttp          # SQLite 版就這樣
# 若走 PostgreSQL 帳號版再加：
pip install asyncpg python-dotenv
```

## 驗收 demo
1. 兩台瀏覽器（或兩分頁）連進同一場遊戲互打。
2. 有人陣亡後，打開排行榜頁能看到剛剛的成績進榜。
3. 重新整理排行榜，名次依擊殺數正確排序。
