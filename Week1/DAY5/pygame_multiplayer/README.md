# pygame 多人射擊小遊戲

多人 2D 射擊：Server 1 台 + 多個 Client，含 HP / Buff 道具 / 追蹤子彈 / 軌道護盾 / 聊天視窗。

## 檔案結構
```
pygame_multiplayer/
├── constants.py   # 全部共用常數
├── server.py      # 權威伺服器：物理、碰撞、道具、per-client 發送 queue
├── client.py      # 入口：show_lobby() → 連線 → run_game()
├── lobby.py       # pygame 大廳：Tab 切換欄位、支援中文 ID
├── game.py        # pygame 遊戲主場景
└── README.md
```

## 玩法

**基本**
- `WASD` 移動，**按住滑鼠左鍵** 自動連射（射速由 server 冷卻控制）
- 每發子彈 5 傷害，100 HP → 20 發打死
- 死亡 → 「GAME OVER」畫面 → 按 Enter 隨機重生

**道具（地上隨機刷新）**
| 顏色 | 標記 | 效果 |
|---|---|---|
| 綠 | `+` | **HP 補血 +25**，同時體積 **變大**（吃越多越大，最多 +20 px）|
| 橘 | `R` | **快速射擊** 8 秒：冷卻從 0.3s → 0.09s |
| 青 | `S` | **加速移動** 8 秒：走路速度 ×1.7 |
| 紫 | `O` | **軌道護盾** 8 秒：3 顆彈丸繞你旋轉，碰到敵人扣 6 血 |
| 黃 | `H` | **追蹤子彈** 8 秒：期間打出的子彈會自動轉向最近敵人 |

**體積成長：** 血包吃多 → 大隻 → 打人更容易碰到 → 但也更容易被打到（hitbox 一起放大）。

**聊天**
- 右下角**半透明聊天視窗**，永遠顯示最近 7 則訊息
- 按 `Enter` 開輸入，再按 Enter 送出。支援中文 IME
- 送出的訊息同時會浮在自己頭上 5 秒（給周圍玩家看得到誰講的）

**畫面**
- 相機置中；左下角小地圖 + 目前視野框
- 準心：黑色十字 + 紅色中心點，跟著滑鼠
- 左上血條 / 血條下方顯示所有啟用中的 Buff 與剩餘秒數
- `F11` 切換全螢幕（用 pygame.SCALED 自動 scale）

## 安裝
```bash
pip install pygame
```

## 執行

### Server
```bash
python server.py
```

### Client
```bash
python client.py
```
大廳操作：
- 點欄位輸入 / **Tab 切換** IP ↔ ID
- 造型 / 顏色 點選（黃框標示目前選擇）
- Enter 或點連線鈕

跨電腦：Server 主機防火牆放行 TCP 5555，兩台同網段。

## 隱藏指令（金手指）

在聊天欄輸入指令：

| 指令 | 效果 |
|---|---|
| `/super` | 開啟金手指：ID 前綴 `[卍煞氣a傳說卍]`、ID 彩虹閃爍、子彈彩虹、自動回血 33 HP/s |
| `/exitsuper` | 關閉金手指 |
| `/快速射擊` | 切換永久快速射擊模式（無時間限制）|
| `/跑快快` | 開啟永久加速移動 |
| `/跑慢慢` | 關閉永久加速 |
| `/變大` | 直接把體積調到最大 |
| `/變小` | 直接把體積歸零 |

指令本身不會顯示在聊天，會轉成系統訊息廣播給所有人看。

## 等級系統

- Level 1 → Level 100，每級 max HP +5、傷害 +1
- 撿血包 +10 XP、撿 Buff 道具 +20 XP
- 升到下一級所需經驗：`20 + level * 3`
- 每升 10 級（10、20、30 ... 90、100）子彈會**換一種形狀 + 加速**：
  0 → 紅圓, 1 → 橘光暈圓, 2 → 黃方, 3 → 綠三角, 4 → 青菱形,
  5 → 藍五邊形, 6 → 紫六邊形, 7 → 粉五芒星, 8 → 血紅六芒星, 9 → **傳說金星**（帶光暈）
- 頭頂顯示 `Lv N` 前綴，左上有 XP 條 + 傷害顯示

## 擊殺公告

有人被打死時右上角會顯示「**擊殺者** 擊殺了 **被擊殺者**」，名字用玩家自己的顏色 render，金手指狀態會帶前綴。訊息保留 6 秒後自動淡出。

## 通訊協定

TCP + `\n` 分隔的 UTF-8 JSON。

| 方向 | type | 主要欄位 |
|---|---|---|
| C → S | `join`    | `id`, `shape`, `color` |
| C → S | `update`  | `x`, `y` |
| C → S | `shoot`   | `dx`, `dy` |
| C → S | `chat`    | `text` |
| C → S | `respawn` | — |
| S → C | `state`   | `players`, `bullets`, `orbits`, `pickups`, `chat_log`, `now` |

`players[i]` 包含 `hp`, `alive`, `size_bonus`, `buffs`(剩餘秒數 dict)、`chat`, `chat_time`。

## 穩定性設計

- **Per-client 發送 queue**：Server 對每個 client 有獨立 `queue.Queue(maxsize=8)` + 發送 thread。慢客戶端只會丟自己的舊封包，不會拖累其他人。
- **TCP_NODELAY** + **SO_KEEPALIVE**：兩端都開，降低延遲並偵測斷線。
- **dt 上限**：`dt = min(now-last, 0.1)`，卡頓時不會讓子彈瞬移穿人。
- **射擊冷卻**：Server 端 rate limit，防止 client 灌爆封包。

## 參數調整

改 `constants.py`：
- `BUFF_DURATION`：Buff 秒數（現在 8s）
- `SPEED_BUFF_MULT` / `SHOOT_COOLDOWN_RAPID`：Buff 強度
- `ORBIT_COUNT` / `ORBIT_RADIUS`：軌道護盾彈丸數量、半徑
- `HOMING_TURN_RATE` / `HOMING_RANGE`：追蹤子彈靈敏度、鎖定範圍
- `PICKUP_WEIGHTS`：道具生成機率（HP 權重 5，其他各 2）
