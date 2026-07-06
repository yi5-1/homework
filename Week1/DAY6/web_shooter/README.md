# Web 版多人射擊（DAY5 pygame 版的瀏覽器移植）

把 DAY5 的 pygame 遊戲搬進瀏覽器。Server 用 `aiohttp` 同時服務 HTTP 靜態檔 + WebSocket，玩家只要用瀏覽器打開網址就能加入，不用裝任何東西。

## 檔案結構

```
web_shooter/
├── server.py        # aiohttp async server + 30Hz 遊戲 tick
├── constants.py     # server 端常數
├── static/
│   ├── index.html   # 大廳 + Canvas 遊戲畫面
│   └── game.js      # 主 client：Canvas 渲染 + WebSocket + 輸入
└── README.md
```

## 安裝
```bash
pip install aiohttp
```

## 執行
```bash
python server.py
```
顯示 `Web server 開啟於 http://0.0.0.0:8765/`。

**手機、平板、任何電腦** 只要在同網段瀏覽器打開：
```
http://<Server 主機 IP>:8765/
```
就會看到大廳 → 選 ID / 造型 / 顏色 → 按連線 → 開玩。

跨電腦記得放行 Server 主機的 TCP 8765。

## 操作
| 動作 | 操作 |
|---|---|
| 移動 | WASD |
| 射擊 | 按住滑鼠左鍵（有射速冷卻）|
| 打字 | Enter 開啟輸入框，Enter 送出，Esc 取消。**中文直接打**（瀏覽器原生 IME）|
| 全螢幕 | F11（瀏覽器內建）|
| 重生 | 死亡後按 Enter |

## 功能

DAY5 pygame 版的所有玩法都保留：

- 玩家可選 造型 / 顏色 / ID（大廳畫面，網頁直接輸入中文）
- HP 系統 / 死亡 / 重生
- 5 種道具：`hp`（+HP，體積成長）、`rapid`（快速射擊）、`speed`（加速）、`orbit`（軌道護盾 3 顆彈丸）、`homing`（追蹤子彈）
- 等級系統 Lv 1-100，每級 max HP +5、傷害 +1
- 子彈依等級 tier 換形狀 + 加速（圓 → 光暈圓 → 方 → 三角 → 菱形 → 五邊 → 六邊 → 星 → 六芒星 → 傳說金星）
- 頭上血條 + 名字（含 Lv、super 前綴、彩虹閃爍）
- 對話泡泡（5 秒）
- 螢幕左下小地圖 + 目前視野框
- 螢幕右下半透明聊天視窗
- 螢幕右上擊殺公告（含淡出）
- 準心跟著滑鼠

## 隱藏指令（在聊天欄輸入）
| 指令 | 效果 |
|---|---|
| `/super` / `/exitsuper` | 開/關金手指（彩虹 ID、前綴、彩虹子彈、自動回血 33 HP/s）|
| `/快速射擊` | 切換永久快射 |
| `/跑快快` / `/跑慢慢` | 開/關永久加速 |
| `/變大` / `/變小` | 體積直接調到最大 / 最小 |

## 通訊協定 (WebSocket + JSON)

| 方向 | type | 主要欄位 |
|---|---|---|
| C → S | `join`    | `id`, `shape`, `color` |
| C → S | `update`  | `x`, `y` |
| C → S | `shoot`   | `dx`, `dy` |
| C → S | `chat`    | `text` |
| C → S | `respawn` | — |
| S → C | `state`   | `players`, `bullets`, `orbits`, `pickups`, `chat_log`, `kill_feed`, `now` |

Server 30Hz 廣播全體狀態；WebSocket 自帶訊息邊界，比 TCP `\n` 分隔簡潔。

## 移植重點對比

| pygame 版 (DAY5) | Web 版 (DAY6) |
|---|---|
| socket + threading + lock | aiohttp + asyncio（單 event loop 免鎖）|
| TCP + `\n` 分隔 JSON | WebSocket + 訊息邊界內建 |
| 每 client 一個發送 queue | `asyncio.gather(return_exceptions=True)` |
| Server 端 pygame 渲染 | HTML5 Canvas 2D |
| Windows-only IME 修法 | 瀏覽器原生 IME（`isComposing` 判斷）|
| 各 client 要 pip install pygame | 只要瀏覽器 |
