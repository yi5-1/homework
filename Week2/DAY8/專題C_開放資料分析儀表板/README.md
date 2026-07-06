# 專題 C — 開放資料分析儀表板

挑一份公開資料（人口、天氣、票房、YouBike…），做一個能互動切換多種圖表的儀表板。這是門檻最低、最適合先練整合的專題。

**整合**：DAY4（pandas + tkinter）＋ DAY3（matplotlib）＋（加分）DAY6（改成網頁版）
**難度** ★★☆☆ ｜ **建議 1–2 人**

---

## 系統架構（GUI 版）

```
政府開放資料 CSV/Excel  →  pandas 讀進來 + 清理  →  下拉選單選圖表類型
                                                        │
                                    tkinter 視窗嵌 matplotlib（即時換圖）
```

DAY4 的 `10_小作品_湖西鄉人口GUI.py` 已經做到這個骨架（下拉選單切 6 種圖），你的任務是**換一份自己的資料**、加更多分析角度。

---

## 必做功能

1. 用 `pandas.read_csv` / `read_excel` 讀一份**你自己找的**公開資料（不要用湖西鄉那份）。
2. 至少算出 3 個衍生欄位 / 統計（例：成長率、佔比、移動平均、排名）。
3. 至少畫 3 種不同圖表（長條 / 折線 / 圓餅 / 散點擇三）。
4. tkinter GUI：用 `ttk.Combobox` 下拉選單切換圖表，圖直接更新在視窗裡。

## 加分功能

- `filedialog` 讓使用者自己選要載入哪個檔案。
- 加篩選：下拉選「年份 / 地區」，圖跟著只顯示那部分資料。
- 匯出：把目前的圖存成 PNG、把分析結果存成新的 Excel。
- **網頁版**：改用 aiohttp/flask 後端把資料算好回傳 JSON，前端用 Canvas 或表格呈現（參考 `web_basics`）。

---

## 從哪裡改起

| 你要的功能 | 抄這個檔 |
|---|---|
| GUI + 下拉切圖 + 嵌 matplotlib（骨架）| `Week1/DAY4/GUI/10_小作品_湖西鄉人口GUI.py` |
| pandas 讀 Excel + 計算 | `Week1/DAY4/作業-湖西鄉人口圖表統計.py` |
| csv.reader + dict(zip()) 讀法 | `Week1/DAY3/台南人口統計.py` |
| 各種圖表寫法 | `Week1/DAY3/直方圖.py`、`散步圖.py`、`matplotlib改圖.py` |
| `filedialog` 選檔 | `Week1/DAY4/GUI/10_小作品_湖西鄉人口GUI.py` |
| 改成網頁版 | `Week1/DAY6/web_basics/` |

**找資料**：政府資料開放平臺 data.gov.tw、各縣市開放資料，下載 CSV/Excel 即可。

## 需要安裝
```bash
pip install pandas openpyxl matplotlib
# 網頁版再加：pip install aiohttp
```

## 驗收 demo
1. 載入你的資料，說明這是什麼資料、想看什麼。
2. 用下拉選單切換至少 3 種圖，每張圖講一句它看出什麼。
3. （加分）換一份檔 / 篩一個條件，圖即時更新。
