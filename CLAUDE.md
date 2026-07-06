# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

STUST（南臺科技大學）2026 AI 課程的個人練習與作業。這是**教學型 repo**，不是一個統一的應用程式：每個 `Week*/DAY*/` 資料夾對應一天的課程主題，內容多為可獨立執行的教學腳本，難度逐日遞增。沒有 build / lint / test 流程 — 每個檔案都是 `python <檔案>` 直接跑。

學習脈絡（複雜度遞增）：
```
DAY2 語法基礎 → DAY3 迴圈+matplotlib → DAY4 pandas+tkinter GUI
→ DAY5 socket+pygame 多人 → DAY6 aiohttp/flask+DB+WebSocket → DAY7 OpenCV 電腦視覺
```

## Conventions that matter here

- **檔名與程式碼識別字大量使用繁體中文**。例如函式 `def 畢氏定理(a, b)`、變數 `灰色的圖片 = cv2.cvtColor(...)`、類別 `class 影像工具`。這是刻意的教學風格，方便對照課程主題。**新增或修改時沿用這個慣例**，不要把既有的中文命名改成英文。
- 中文字型：matplotlib 與 GUI 統一用 `Microsoft JhengHei`（Windows 內建）。畫圖前若中文顯示為方框，設定 `plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']`。
- 平台是 Windows；預設終端是 PowerShell。
- 教學腳本傾向「一個檔案聚焦一個概念」，循序命名（如 GUI 的 `01_` ～ `10_`）。新增教學檔時延續這個編號 / 單一主題原則。

## Running things

沒有統一入口。依資料夾各自執行：

**基礎腳本（DAY2–4、DAY7）** — 直接跑，相依套件：
```bash
pip install matplotlib pandas openpyxl        # DAY3/DAY4 資料視覺化
pip install opencv-python pillow numpy         # DAY7 電腦視覺（需鏡頭，按 q 離開）
python "Week1/DAY4/GUI/08_小作品_BMI計算機.py"
```

**DAY5 socket / pygame**（先開 server 再開 client；跨機需放行對應 TCP port）：
```bash
python Week1/DAY5/Server.py        # 或 ChatServer.py
python Week1/DAY5/Client.py        # 或 ChatClient.py
# pygame 多人遊戲（TCP 5555，pip install pygame）：
python Week1/DAY5/pygame_multiplayer/server.py
python Week1/DAY5/pygame_multiplayer/client.py
```

**DAY6 web 子專案** — 每個都是獨立的 mini app，**各自有 README 與埠號**：
```bash
# web_basics：aiohttp + SQLite 留言板（DB 自動建立）
pip install aiohttp && python Week1/DAY6/web_basics/server.py        # http://<host>:8765/

# web_shooter：aiohttp + WebSocket + Canvas 多人射擊（瀏覽器即玩）
pip install aiohttp && python Week1/DAY6/web_shooter/server.py       # http://<host>:8765/

# web_auth：aiohttp + PostgreSQL 會員系統（需先設定 .env，見下）
pip install -r Week1/DAY6/web_auth/requirements.txt
python Week1/DAY6/web_auth/server.py                                 # port 由 .env SERVER_PORT

# 電商平台：Flask + PostgreSQL（psycopg2），需先建表
pip install -r "Week1/DAY6/電商平台/requirements.txt"
python "Week1/DAY6/電商平台/init_db.py"    # 建表 + 種子資料（admin / admin123）
python "Week1/DAY6/電商平台/app.py"
```

## Database & secrets setup

用到 PostgreSQL 的子專案（`web_auth`、`電商平台`）都靠 `.env` + `python-dotenv` 讀連線設定，`.env` 已在 `.gitignore`（含密碼，禁止 commit）。

- `web_auth`：`cp Week1/DAY6/web_auth/.env.example Week1/DAY6/web_auth/.env` 後填入 `DB_PASSWORD`。用 `asyncpg` 連線池，資料庫預設 `STUST2026AI`。
- `電商平台`：`config.py` 從環境變數讀 DSN（`DB_NAME` 預設 `shop`），跑 `init_db.py` 建表。
- `web_basics` / `web_shooter`：用 SQLite 或純記憶體，無需設定，DB 檔（`*.db`，已 gitignore）首次執行自動產生。

## Client/server 子專案的架構要點

`pygame_multiplayer/`（DAY5）與 `web_shooter/`（DAY6）是同一款多人射擊遊戲的兩個版本，且是 repo 裡最複雜的程式碼，改動前值得先讀各自的 `README.md`：

- **權威伺服器模型**：server 跑物理、碰撞、道具、等級；client 只送輸入（`join`/`update`/`shoot`/`chat`/`respawn`）、收整體 `state` 廣播。改遊戲邏輯要改 server 端。
- 兩版共用的調參集中在各自的 `constants.py`（Buff 秒數、道具權重、追蹤子彈靈敏度等）。
- DAY5 版：TCP + `\n` 分隔 JSON、per-client 發送 queue + threading。DAY6 版：把同款遊戲移植成 aiohttp + WebSocket + asyncio（單 event loop 免鎖）+ HTML5 Canvas，`README.md` 底部有兩版的移植對照表。
- 兩版都有相同的隱藏聊天指令（`/super`、`/快速射擊`、`/變大` 等）與等級/子彈換形狀系統。

`電商平台/` 是分層 Flask app：`app.py`（路由）/ `models.py`（DB 存取）/ `config.py`（設定）/ `templates/`（Jinja2）/ `static/`，並附 `spec/` 內的系統規格書與 API 設計文件 — 改功能前先對照 spec。
