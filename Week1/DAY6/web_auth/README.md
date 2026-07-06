# 會員系統 — aiohttp + PostgreSQL

前後端分離的最小會員系統：**只有註冊 + 登入兩個 API**，密碼明文儲存（教學用），資料放 PostgreSQL。

## 三層架構

```
┌──────────────┐   HTTP    ┌──────────────┐  asyncpg  ┌──────────────┐
│   瀏覽器     │  ──────►  │   aiohttp    │  ──────►  │  PostgreSQL  │
│ (index.html) │  ◄──────  │  (server.py) │  ◄──────  │  STUST2026AI │
└──────────────┘           └──────────────┘           └──────────────┘
    前端                       後端                       資料庫
```

## 檔案

| 檔案 | 用途 |
|---|---|
| `server.py` | aiohttp 後端 + PostgreSQL 連線池 |
| `static/index.html` | 前端頁面：註冊 / 登入 切換 tab |
| `.env.example` | 環境變數範本，複製成 `.env` 填自己的 |
| `.env` | 你的實際設定（**不會被 push**，已在 `.gitignore`）|
| `requirements.txt` | 需要的 pip 套件 |

## 前置準備

### 1) 裝 PostgreSQL 並啟動
Windows 直接下載安裝：<https://www.postgresql.org/download/windows/>  
安裝過程會問要設定的 `postgres` 使用者密碼，**記下來**。

### 2) 建立資料庫
用附贈的 `psql` 或 pgAdmin，執行：
```sql
CREATE DATABASE "STUST2026AI";
```
（大小寫要與 `.env` 一致；用雙引號避免 PostgreSQL 自動轉小寫）

### 3) 複製 `.env.example` → `.env`
把 `DB_PASSWORD` 換成你剛才設的密碼。

### 4) 安裝 Python 套件
```bash
pip install -r requirements.txt
```

## 執行
```bash
python server.py
```
成功會看到：
```
已連上 PostgreSQL localhost:5432/STUST2026AI
Server 開啟於 http://127.0.0.1:8001/
```

瀏覽器打開 <http://127.0.0.1:8001/> 就能玩。

## API 規格

| Method | URL | Body | 成功回應 |
|---|---|---|---|
| POST | `/api/register` | `{"username","password"}` | `{"ok":true,"message":"..."}` |
| POST | `/api/login`    | `{"username","password"}` | `{"ok":true,"message":"..."}` |

錯誤都回 `{"ok":false,"error":"..."}`，HTTP status 400 或 401。

## 資料表

```sql
CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    password   TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

驗一下有沒有存進去：
```bash
psql -U postgres -d STUST2026AI -c "SELECT * FROM users;"
```

## 教學重點對照表

| 教學主題 | 對應程式碼 |
|---|---|
| 環境變數 | `load_dotenv()` + `os.getenv()` |
| PostgreSQL 連線池 | `asyncpg.create_pool(...)` |
| 建表 | `CREATE TABLE IF NOT EXISTS ...` |
| 佔位符（防 SQL Injection）| `INSERT ... VALUES ($1, $2)` |
| 唯一鍵處理 | `except asyncpg.UniqueViolationError` |
| 查詢單筆 | `await conn.fetchrow("SELECT ... WHERE ...")` |
| 前端 fetch JSON | `fetch(url, {method:'POST', body: JSON.stringify(...)})` |
| Tab 切換 UI | `classList.toggle('hidden', ...)` |

## 進階可加的東西（給有餘裕的學生）
- 密碼改用 `hashlib.pbkdf2_hmac` hash 後存，比對時 hash 再比對
- 登入成功發 session cookie 或 JWT
- 加「已登入頁面」顯示使用者名字
- 加「登出」按鈕
- 加 CAPTCHA 或登入次數限制
