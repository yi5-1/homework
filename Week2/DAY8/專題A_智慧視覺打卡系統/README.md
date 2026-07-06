# 專題 A — 智慧視覺打卡系統

用鏡頭把「有沒有人在畫面前」變成一筆出勤紀錄，存進資料庫，最後畫出出勤統計圖。

**整合**：DAY7（OpenCV 鏡頭）＋ DAY6 或 DAY4（存資料庫 / GUI）＋ DAY3（統計圖表）＋ DAY2（函式）
**難度** ★★★☆ ｜ **建議 2–3 人**

---

## 系統架構

```
鏡頭 (OpenCV)  →  偵測到人/按鍵打卡  →  寫一筆 (姓名, 時間) 進資料庫
                                                    │
                            matplotlib 讀資料庫  →  出勤長條圖 / 圓餅圖
```

最小可行版本可以「按鍵盤打卡」就好；進階再做「自動偵測畫面有變化才打卡」。

---

## 必做功能

1. 開鏡頭即時顯示畫面（`cv2.VideoCapture(0)`，按 `q` 離開）。
2. 打卡：輸入姓名後，按一個鍵把「姓名 + 現在時間」存起來。
   - 存法二選一：SQLite（參考 `web_basics`）或直接寫 CSV（參考 DAY3 `開啟檔案.py`）。
3. 查詢：能列出今天所有打卡紀錄。
4. 統計圖：用 matplotlib 畫「每個人打卡次數」長條圖或「出勤/缺席」圓餅圖。

## 加分功能

- 用畫面**影格差異**（前後兩張灰階相減）自動判斷「有人來了」才觸發打卡，不用手按。
- 用 DAY4 的 tkinter GUI 包起來：左邊鏡頭畫面（`FigureCanvasTkAgg` 或 `PIL.ImageTk`），右邊按鈕 + 紀錄清單。
- 遲到判斷：超過設定時間打卡標記「遲到」，統計圖用不同顏色。
- 用 `pandas` 匯出當月出勤 Excel。

---

## 從哪裡改起

| 你要的功能 | 抄這個檔 |
|---|---|
| 開鏡頭 + 逐格處理 | `Week1/DAY7/視覺.py` |
| 影格差異 / 灰階 | `Week1/DAY7/視覺.py`（`cvtColor`、`Canny` 那段）|
| 把鏡頭嵌進 tkinter | `Week1/DAY7/tkinter影像處理工具.py`（用 `PIL.ImageTk` 貼到 Canvas）|
| 寫 / 讀 SQLite | `Week1/DAY6/web_basics/server.py`（資料庫層那段）|
| 存 / 讀 CSV | `Week1/DAY3/開啟檔案.py`、`台南人口統計.py` |
| 畫長條 / 圓餅圖 | `Week1/DAY3/直方圖.py`、`台南人口統計.py`（圓餅）|
| GUI 版面 | `Week1/DAY4/GUI/10_小作品_湖西鄉人口GUI.py` |

## 需要安裝
```bash
pip install opencv-python pillow matplotlib pandas
```

## 驗收 demo
1. 跑起來看到鏡頭畫面。
2. 用兩個名字各打卡幾次。
3. 顯示今天紀錄清單。
4. 跳出一張出勤統計圖，數字對得起剛剛打的卡。
