# 專題 E — 即時視覺監控站

一台電腦接鏡頭當「攝影主機」，把即時影像透過網路推出去，任何人用瀏覽器打開網址就能同時看到畫面。等於自己做一個陽春版監視器 / 直播。

**整合**：DAY7（OpenCV 擷取 + 影像處理）＋ DAY6（aiohttp + WebSocket + 瀏覽器）＋ DAY5（多 client 廣播觀念）
**難度** ★★★★ ｜ **建議 2–3 人**

---

## 系統架構

```
鏡頭 (OpenCV)  →  每格轉成 JPEG → base64  →  aiohttp server
                                                  │  WebSocket 廣播
                        多台瀏覽器 ◄─────────────┘  <img> 或 Canvas 顯示
```

跟 `web_shooter` 幾乎一樣的骨架（server 定時廣播狀態給所有 WebSocket client），只是廣播的內容從「遊戲狀態」換成「一張影像」。

---

## 必做功能

1. server 端用 OpenCV 開鏡頭，每格影像用 `cv2.imencode('.jpg', frame)` 壓成 JPEG。
2. 把 JPEG 轉 base64，透過 WebSocket 定時（例：每 100ms）廣播給所有連線的瀏覽器。
3. 瀏覽器端收到就更新 `<img>` 的 `src`（或畫到 Canvas），呈現即時畫面。
4. 支援**多個瀏覽器同時觀看**同一路影像。

## 加分功能

- 前端按鈕切換濾鏡：原圖 / 灰階 / Canny 邊緣 / 模糊（server 端套 DAY7 學的處理再送）。
- 顯示線上觀看人數（server 記 WebSocket 連線數並廣播）。
- 動作偵測：畫面有大變化時，server 側存一張 JPEG 快照 + 記一筆時間進 DB（參考 web_basics）。
- FPS / 延遲顯示。

---

## 從哪裡改起

| 你要的功能 | 抄這個檔 |
|---|---|
| aiohttp + WebSocket 廣播骨架 | `Week1/DAY6/web_shooter/server.py`（把廣播 payload 換成影像）|
| 前端 WebSocket 接收 + 顯示 | `Week1/DAY6/web_shooter/static/game.js`（改成更新 `<img>`）|
| 開鏡頭 + 影像處理 | `Week1/DAY7/視覺.py`（`imencode`、`cvtColor`、`Canny`）|
| 存快照 / 記錄進 DB | `Week1/DAY6/web_basics/server.py` |
| 多人聊天室廣播觀念 | `Week1/DAY5/ChatServer.py` |

> **注意**：影像比遊戲狀態大很多。先把畫面**縮小**（例：640×480 → 320×240）、JPEG 品質調低，再調廣播頻率，否則會很卡。這正好練 DAY6 「每 client 一個發送、慢客戶端不拖累別人」的觀念。

## 需要安裝
```bash
pip install aiohttp opencv-python numpy
```

## 驗收 demo
1. server 主機接鏡頭跑起來。
2. 兩台裝置（手機 + 電腦）用瀏覽器連同一個網址，都看到即時畫面。
3. （加分）在網頁上切換濾鏡，所有觀看端一起變。
