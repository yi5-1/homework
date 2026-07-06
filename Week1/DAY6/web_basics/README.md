# Hello Web — 三層架構留言板

三個檔案帶你認識 Web 開發：**前端 / 後端 / 資料庫**分離。

## 三層架構圖

```
┌──────────────┐     HTTP Request      ┌──────────────┐   SQL   ┌────────────┐
│  瀏覽器      │  ─────────────────►   │  aiohttp     │ ──────► │  SQLite    │
│ (index.html) │  ◄─────────────────   │  (server.py) │ ◄────── │(messages.db)│
│  + JS fetch  │     HTTP Response     │              │         │            │
└──────────────┘                       └──────────────┘         └────────────┘
   前端 (Client)                       後端 (Server)             資料庫
   HTML 畫面 + JS                       Python                    儲存資料
```

**為什麼要分層？**
- 前端只負責畫面 → 任何裝置的瀏覽器都能開
- 後端只負責邏輯 → 換一種前端（App、桌面）也能重用
- 資料庫只負責存資料 → 程式關掉重開，資料還在

## 檔案

| 檔案 | 角色 |
|---|---|
| `server.py` | 後端：aiohttp 收 HTTP request，跟 SQLite 讀寫 |
| `static/index.html` | 前端：HTML 畫面 + CSS 樣式 + JS 呼叫 API |
| `messages.db` | 資料庫檔（程式第一次跑會自動產生）|

## 安裝

```bash
pip install aiohttp
```
（`sqlite3` 是 Python 內建，不用安裝）

## 執行

```bash
python server.py
```

瀏覽器打開 <http://127.0.0.1:8000/>

## 前端 → 後端 溝通說明

前端用 **`fetch()`** 跟後端說話。兩種常見動作：

| HTTP 方法 | URL | 意思 |
|---|---|---|
| **GET** | `/api/messages` | 「給我所有訊息」→ 後端回傳 JSON 陣列 |
| **POST** | `/api/messages` | 「幫我新增一筆」→ body 帶 `{name, text}` JSON |

範例 fetch：

```javascript
// GET：拉資料
const res = await fetch('/api/messages');
const data = await res.json();   // [{name, text, created_at}, ...]

// POST：送資料
await fetch('/api/messages', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ name: '小明', text: '哈囉' })
});
```

## 後端 → 資料庫 溝通說明

Python 用 **`sqlite3`** 模組（內建，不用裝）。

```python
import sqlite3
conn = sqlite3.connect("messages.db")

# 查資料
rows = conn.execute("SELECT name, text FROM messages").fetchall()

# 存資料（用 ? 佔位符防 SQL injection）
conn.execute("INSERT INTO messages (name, text) VALUES (?, ?)", ("小明", "哈囉"))
conn.commit()

conn.close()
```

## 對應到本 demo 的元素

前端有的東西：
- **標題** (Label) — `<h1>Hello World 留言板</h1>`
- **輸入框** (Input) — `<input id="name">` `<input id="text">`
- **按鈕** (Button) — `<button onclick="送出訊息()">送出</button>`
- **顯示區** (Label) — `<div id="messages">` 由 JS 動態填內容

後端有的 API：
- `GET  /`              → 回傳 index.html
- `GET  /api/messages`  → 回 JSON 訊息列表
- `POST /api/messages`  → 新增一筆訊息

資料庫有的表：
```sql
CREATE TABLE messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT,
    text       TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 動手玩看看

1. 開啟頁面 → 看到「載入中...」 → 立刻變成「（還沒有留言...）」
2. 輸入名字 + 訊息 → 按送出 → 訊息立刻顯示在下面
3. 關掉 server (`Ctrl+C`)，重新開 → **訊息還在**（因為存在 `messages.db`）
4. 用檔案總管把 `messages.db` 打開（用 [DB Browser for SQLite](https://sqlitebrowser.org/) 或 VS Code 的 SQLite 外掛）→ 直接看到你剛才留的資料
