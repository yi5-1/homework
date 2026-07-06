# 專題 C 起手式：開放資料分析儀表板（能跑的最小骨架）
#
# 現在會做的事：
#   - 內建一份範例資料（六都人口），用 tkinter 視窗 + 下拉選單切換 3 種圖
#   - 圖直接畫在視窗裡（FigureCanvasTkAgg），切換即時更新
#
# 你要接手加的：
#   - 換成「你自己找的」公開資料（data.gov.tw 下載 CSV/Excel）
#   - 用 filedialog 讓使用者選檔（下方已留按鈕與 TODO）
#   - 加篩選、匯出 PNG/Excel、或改成網頁版

import tkinter as tk
from tkinter import ttk, filedialog

import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]  # 中文不變方框
plt.rcParams["axes.unicode_minus"] = False


def 載入範例資料():
    # TODO：把這段換成 pd.read_csv("你的檔.csv") 或 pd.read_excel(...)
    return pd.DataFrame({
        "縣市": ["台北", "新北", "桃園", "台中", "台南", "高雄"],
        "人口": [247, 400, 227, 282, 186, 273],   # 單位：萬
        "面積": [272, 2052, 1221, 2215, 2192, 2952],  # 平方公里
    })


class 儀表板:
    def __init__(self, 資料):
        self.df = 資料

        self.root = tk.Tk()
        self.root.title("開放資料分析儀表板")
        self.root.geometry("820x600")

        控制列 = tk.Frame(self.root)
        控制列.pack(fill="x", padx=10, pady=8)

        tk.Label(控制列, text="圖表類型：").pack(side="left")
        self.圖表選單 = ttk.Combobox(
            控制列, state="readonly",
            values=["長條圖：各縣市人口", "折線圖：各縣市人口", "圓餅圖：人口佔比"],
        )
        self.圖表選單.current(0)
        self.圖表選單.pack(side="left")
        self.圖表選單.bind("<<ComboboxSelected>>", lambda e: self.更新圖表())

        tk.Button(控制列, text="載入我的檔案…", command=self.載入檔案).pack(side="left", padx=10)

        self.fig = plt.Figure(figsize=(7, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        self.更新圖表()

    def 更新圖表(self):
        self.ax.clear()
        選擇 = self.圖表選單.get()
        縣市 = self.df["縣市"]
        人口 = self.df["人口"]

        if 選擇.startswith("長條圖"):
            self.ax.bar(縣市, 人口, color="#4C72B0")
            self.ax.set_ylabel("人口（萬）")
        elif 選擇.startswith("折線圖"):
            self.ax.plot(縣市, 人口, marker="o", color="#DD8452")
            self.ax.set_ylabel("人口（萬）")
        else:  # 圓餅圖
            self.ax.pie(人口, labels=縣市, autopct="%1.1f%%")

        self.ax.set_title(選擇)
        self.fig.tight_layout()
        self.canvas.draw()
        # TODO：資料換掉後，欄位名（"縣市"/"人口"）記得一起改

    def 載入檔案(self):
        路徑 = filedialog.askopenfilename(
            filetypes=[("資料檔", "*.csv *.xlsx"), ("所有檔案", "*.*")]
        )
        if not 路徑:
            return
        # TODO：讀進來後對應好欄位名，再 self.更新圖表()
        if 路徑.lower().endswith(".xlsx"):
            self.df = pd.read_excel(路徑)
        else:
            self.df = pd.read_csv(路徑)
        print("已載入：", 路徑, "欄位：", list(self.df.columns))
        self.更新圖表()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    儀表板(載入範例資料()).run()
