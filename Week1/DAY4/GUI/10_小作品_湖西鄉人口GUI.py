# 教學重點：tkinter + matplotlib 整合 + filedialog 檔案選擇器 + 下拉式選單切換圖表
# 流程：點按鈕 → 選 xlsx → 用下拉選單切換要看的圖

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

window = tk.Tk()
window.title("湖西鄉人口分析")
window.geometry("1100x650")

# ====== 上方控制列 ======
上方 = tk.Frame(window)
上方.pack(side="top", fill="x", pady=5)

路徑顯示 = tk.Label(上方, text="（尚未選擇檔案）", fg="gray")
路徑顯示.pack(side="left", padx=10)

tk.Label(上方, text="圖表：").pack(side="left")

# 下拉式選單可選的圖表類型
圖表選項 = [
    "出生 vs 死亡 差方圖 (bar)",
    "總人口數 折線圖",
    "出生數 折線圖",
    "死亡數 折線圖",
    "遷入 / 遷出 折線圖",
    "男 / 女 人口 折線圖",
]
選單 = ttk.Combobox(上方, values=圖表選項, state="readonly", width=28)
選單.current(0)
選單.pack(side="left", padx=5)

# ====== 圖表區 ======
圖表區 = tk.Frame(window)
圖表區.pack(side="top", fill="both", expand=True)

# 共享狀態：目前的資料、目前的畫布
資料 = {"df": None}
目前畫布 = {"obj": None}

def 取得欄位(df):
    # 把 12 個欄位拆成有名字的 list，方便後續引用
    return {
        "年":   df.iloc[:, 0].astype(int).tolist(),
        "月":   df.iloc[:, 1].astype(int).tolist(),
        "總戶數": df.iloc[:, 2].astype(int).tolist(),
        "總人口": df.iloc[:, 3].astype(int).tolist(),
        "男":   df.iloc[:, 4].astype(int).tolist(),
        "女":   df.iloc[:, 5].astype(int).tolist(),
        "遷入": df.iloc[:, 6].astype(int).tolist(),
        "遷出": df.iloc[:, 7].astype(int).tolist(),
        "出生": df.iloc[:, 8].astype(int).tolist(),
        "死亡": df.iloc[:, 9].astype(int).tolist(),
    }

def 畫圖():
    if 資料["df"] is None:
        return   # 還沒選檔案就不畫

    d = 取得欄位(資料["df"])
    labels = [f'{y}/{m:02d}' for y, m in zip(d["年"], d["月"])]
    x = range(len(labels))

    # 清掉舊圖
    if 目前畫布["obj"] is not None:
        目前畫布["obj"].get_tk_widget().destroy()

    fig, ax = plt.subplots(figsize=(11, 4.5))
    選擇 = 選單.get()

    if 選擇 == "出生 vs 死亡 差方圖 (bar)":
        diff = [b - dd for b, dd in zip(d["出生"], d["死亡"])]
        colors = ['#2E86DE' if v >= 0 else '#E74C3C' for v in diff]
        ax.bar(x, diff, color=colors)
        ax.axhline(0, color='black', linewidth=0.8)
        ax.set_ylabel('出生 - 死亡 (人)')
        ax.set_title('每月自然增加人口 (出生 - 死亡)')

    elif 選擇 == "總人口數 折線圖":
        ax.plot(x, d["總人口"], color='#2E86DE', marker='o', markersize=3)
        ax.set_ylabel('人口數')
        ax.set_title('總人口數變化')

    elif 選擇 == "出生數 折線圖":
        ax.plot(x, d["出生"], color='#27AE60', marker='o', markersize=3)
        ax.set_ylabel('出生數')
        ax.set_title('每月出生數')

    elif 選擇 == "死亡數 折線圖":
        ax.plot(x, d["死亡"], color='#E74C3C', marker='o', markersize=3)
        ax.set_ylabel('死亡數')
        ax.set_title('每月死亡數')

    elif 選擇 == "遷入 / 遷出 折線圖":
        ax.plot(x, d["遷入"], color='#27AE60', marker='o', markersize=3, label='遷入')
        ax.plot(x, d["遷出"], color='#E74C3C', marker='o', markersize=3, label='遷出')
        ax.set_ylabel('人數')
        ax.set_title('遷入 vs 遷出')
        ax.legend()

    elif 選擇 == "男 / 女 人口 折線圖":
        ax.plot(x, d["男"], color='#2E86DE', marker='o', markersize=3, label='男')
        ax.plot(x, d["女"], color='#E91E63', marker='o', markersize=3, label='女')
        ax.set_ylabel('人口數')
        ax.set_title('男 vs 女 人口')
        ax.legend()

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=75, fontsize=7)
    ax.set_xlabel('年/月')
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=圖表區)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    目前畫布["obj"] = canvas

def 選檔案():
    path = filedialog.askopenfilename(
        title="選擇湖西鄉人口資料",
        filetypes=[("Excel 檔", "*.xlsx *.xls"), ("所有檔案", "*.*")]
    )
    if not path:
        return
    try:
        資料["df"] = pd.read_excel(path, header=None, skiprows=1)
    except Exception as e:
        messagebox.showerror("讀檔失敗", str(e))
        return
    路徑顯示.config(text=path, fg="black")
    畫圖()

tk.Button(上方, text="選擇檔案", command=選檔案).pack(side="right", padx=10)

# 下拉選單一改 → 重畫圖
選單.bind("<<ComboboxSelected>>", lambda e: 畫圖())

window.mainloop()
