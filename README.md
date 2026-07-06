# 2026 AI - STUST 學習筆記

南臺科技大學 (STUST) 2026 AI 課程的個人練習與作業 repo，記錄從 Python 基礎到資料視覺化的學習過程。

---

## 環境需求

```bash
pip install matplotlib pandas openpyxl
```

中文字型預設使用 `Microsoft JhengHei`（Windows 內建）。

---

## 目錄結構

```
project/
├── hello.md                          # Markdown 練習
├── Week1/
│   ├── DAY2/                         # Python 基礎：變數、條件、邏輯、函式
│   ├── DAY3/                         # 迴圈、列表、檔案 I/O、matplotlib 圖表
│   └── DAY4/                         # Excel 讀取 + 真實人口資料分析
└── README.md
```

---

## Week 1

### DAY 2 — Python 基礎語法

主題：變數、型別、運算子、條件判斷、布林邏輯、函式與模組。

| 檔案 | 內容 |
|---|---|
| `變數教學.py` | 變數宣告、運算子、`type()` 查看型別 |
| `變數類型.py` | 同一變數放入 `int` / `float` / `str` 時的型別變化 |
| `四則運算.py` | 字串相加 (`+`) 的範例 |
| `輸入.py` | `input()` 取得使用者輸入，搭配 `float()` 做加法 |
| `布林比較.py` | `>`、`<`、`>=`、`<=`、`==` 比較運算子 |
| `邏輯.py` | `and`、`or` 布林邏輯運算 |
| `邏輯題目and.py` | 情境題：超商買珍奶（年齡 ∧ 金錢） |
| `邏輯題目or.py` | 情境題：出門帶傘（下雨 ∨ 大太陽） |
| `如果條件.py` | `if / elif / else` 三向分支 |
| `文字遊戲(手搓版).py` | 用 `input` + `if` 做簡單心情回應遊戲 |
| `畢氏定理.py` | 自訂函式 `畢氏定理(a, b)` 計算斜邊；展示 `import math as 數學` |
| `斜向拋射.py` | 計算飛行時間 / 最大高度 / 水平射程，使用 `math.radians`、`math.sin` |
| `main.py` | 跨檔 `import 畢氏定理` 模組呼叫範例 |

### DAY 3 — 迴圈、列表、檔案 I/O、matplotlib

主題：流程控制、容器型別、CSV 處理、基礎資料視覺化。

| 檔案 | 內容 |
|---|---|
| `for迴圈.py` | `range()` 與 list 迭代寫法 |
| `while迴圈.py` | `while` 配合 `time.sleep` 做倒數 |
| `列表.py` | List 宣告、索引取值、`len()`、`type()` |
| `列表的append.py` | `append` 收集資料再繪製二次函式折線圖 |
| `開啟檔案.py` | 原始 `open()` + `split()` 拆 CSV，理解編碼與分隔 |
| `台南人口統計.py` | 用 `csv.reader` + `dict(zip(header, row))` 讀取台南人口資料，畫出各區人口佔比圓餅圖 |
| `matplotlib 折線圖教學.py` | matplotlib `plt.plot` 入門 |
| `matplotlib改圖.py` | 加上中文字型、`xlim` / `ylim` / 標題 / 軸標籤 |
| `直方圖.py` | `plt.hist` 繪製成績分布 |
| `散步圖.py` | `plt.scatter` 散點圖 |
| `985ed9fd-…csv` | 台南市各區人口統計資料來源檔 |

### DAY 4 — Excel 讀取與人口分析作業

| 檔案 | 內容 |
|---|---|
| `data.xlsx` / `data.csv` | 湖西鄉（澎湖）逐月人口統計資料。註：兩個檔案內容相同，皆為 xlsx 二進位格式 |
| `作業-湖西鄉人口圖表統計.py` | **作業**：用 `pandas.read_excel` 讀入 65 個月的資料，計算「出生 − 死亡」的自然增加數，繪製單條長條圖：正成長朝上 (藍)，負成長朝下 (紅)，並以 `axhline(0)` 標出 0 軸 |

執行結果：65 個月中 19 個月正成長、39 個月負成長、7 個月持平。湖西鄉人口呈現自然減少趨勢。

#### GUI 子資料夾 — tkinter 教學

每個檔案聚焦一個概念，循序漸進。tkinter 是 Python 內建模組，**不用額外安裝**。

| 檔案 | 主題 |
|---|---|
| `01_第一個視窗.py` | `Tk()` 建立視窗、`title`、`geometry`、`mainloop` |
| `02_Label文字標籤.py` | `Label` 顯示文字，字型 / 顏色 / 背景色設定 |
| `03_Button按鈕.py` | `Button` 搭配 `command=函式名` 觸發動作 |
| `04_Entry輸入框.py` | `Entry` 取得使用者輸入，用 `.get()` 拿值 |
| `05_pack排版.py` | `pack()` 的 `side` 方向參數（top/bottom/left/right）|
| `06_grid格狀排版.py` | `grid(row, column)` 表格式排版，`columnspan` 跨欄 |
| `07_messagebox彈出視窗.py` | 提示 / 警告 / 錯誤 / 是非詢問四種彈窗 |
| `08_小作品_BMI計算機.py` | 綜合練習：把上面所有元件組成 BMI 小工具 |
| `09_小作品_斜向拋射.py` | 把 DAY2 的斜向拋射函式套上 GUI，輸入 v0、角度即可算出 T / H / R |
| `10_小作品_湖西鄉人口GUI.py` | 整合 `filedialog` 檔案選擇器 + `FigureCanvasTkAgg` 嵌入 matplotlib + `ttk.Combobox` 下拉選單切換 6 種圖（差方圖 / 總人口 / 出生 / 死亡 / 遷入遷出 / 男女）|

### DAY 5 — Socket 網路程式

| 檔案 / 資料夾 | 內容 |
|---|---|
| `Server.py` / `Client.py` | 最小 TCP echo server / client |
| `ChatServer.py` / `ChatClient.py` | 多人聊天室（threading + broadcast）|
| `pygame_multiplayer/` | pygame 多人 2D 遊戲：Server + Client，WASD 移動、小地圖、聊天泡泡。詳見資料夾內 `README.md` |

### DAY 6 — Web 基礎 + Web 版多人遊戲

| 檔案 / 資料夾 | 內容 |
|---|---|
| `web_basics/` | **Web 入門**：三層架構 demo 留言板 — HTML/JS 前端 + aiohttp 後端 + SQLite。教 fetch、GET/POST、JSON、SQL 基本語法 |
| `web_auth/` | **PostgreSQL + 環境變數**：最小會員系統，只有註冊 + 登入兩個 API，`asyncpg` 連線池 + `.env` 讀密碼 |
| `web_shooter/` | **進階**：把 DAY5 的 pygame 遊戲移植到瀏覽器：`aiohttp` + WebSocket + HTML5 Canvas。所有人只要瀏覽器打開 `http://<host>:8765/` 就能玩，不用裝 pygame |

---

## hello.md

Markdown 語法初體驗，練習標題與項目符號。

---

## 學習脈絡

```
DAY2 語法基礎  →  DAY3 迴圈 + 視覺化  →  DAY4 pandas + tkinter GUI  →  DAY5 socket + pygame 多人  →  DAY6 aiohttp + WebSocket + Canvas
   (變數/條件)        (列表/檔案/plt)         (Excel/作業/GUI)              (TCP/threading/pygame)         (瀏覽器多人遊戲)
```

每個檔名都用中文命名，方便對照當天課程主題快速回頭翻閱。
