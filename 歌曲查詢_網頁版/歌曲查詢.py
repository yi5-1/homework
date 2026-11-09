"""
歌曲查詢 - 日文歌詞搜尋與中文翻譯匯出工具
========================================
安裝相依套件：
    pip install requests beautifulsoup4

使用流程：
    1. 輸入日文歌名（歌手欄可留空，填了可縮小搜尋範圍）
    2. 按「搜尋」，在下方結果清單雙擊要查的那首歌，載入原文歌詞
    3. 按「複製原文」把日文歌詞複製起來，拿去請 Claude 幫忙翻譯成中文
    4. 把翻譯結果貼進「中文翻譯」欄位，每一行對應原文的每一行
    5. 按「匯出」存成 .txt（原文／翻譯逐行對照）

歌詞來源：J-Lyric.net (https://j-lyric.net/)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

搜尋網址 = "https://j-lyric.net/search.php"
標頭 = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}
字型 = ("Microsoft JhengHei", 11)


def 搜尋歌曲(歌名, 歌手=""):
    """在 J-Lyric.net 搜尋歌曲，回傳 [(標題, 歌手, 連結), ...]"""
    參數 = {
        "ex": "on",
        "kt": 歌名, "ct": 2,
        "ka": 歌手, "ca": 2,
        "kl": "", "cl": 2,
    }
    回應 = requests.get(搜尋網址, params=參數, headers=標頭, timeout=10)
    回應.raise_for_status()
    湯 = BeautifulSoup(回應.content, "html.parser")

    結果 = []
    for 區塊 in 湯.select("div.bdy"):
        連結標籤 = 區塊.select_one("p.mid a")
        歌手標籤 = 區塊.select_one("p.sml a")
        if not 連結標籤:
            continue
        結果.append((
            連結標籤.get_text(strip=True),
            歌手標籤.get_text(strip=True) if 歌手標籤 else "未知歌手",
            urljoin(搜尋網址, 連結標籤["href"]),
        ))
    return 結果


def 抓取歌詞(網址):
    """讀取歌詞頁面，回傳 (標題, 歌手, 歌詞文字)"""
    回應 = requests.get(網址, headers=標頭, timeout=10)
    回應.raise_for_status()
    湯 = BeautifulSoup(回應.content, "html.parser")

    歌詞區 = 湯.select_one("p#Lyric")
    if 歌詞區 is None:
        raise ValueError("找不到歌詞內容，網站結構可能已變更")

    for 換行 in 歌詞區.find_all("br"):
        換行.replace_with("\n")
    歌詞文字 = 歌詞區.get_text().strip("\n")

    標題文字 = 湯.title.get_text(strip=True) if 湯.title else ""
    標題, _, 歌手 = 標題文字.partition("／")
    歌手 = 歌手.replace("歌詞", "").strip()
    return 標題.strip() or "未知歌名", 歌手 or "未知歌手", 歌詞文字


class 歌曲查詢視窗:
    def __init__(self, root):
        self.root = root
        root.title("歌曲查詢 - 日文歌詞搜尋與翻譯匯出")
        root.geometry("760x680")

        self.搜尋結果 = []  # [(標題, 歌手, 連結), ...]
        self.目前歌名 = ""
        self.目前歌手 = ""

        self._建立搜尋區()
        self._建立結果區()
        self._建立歌詞區()
        self._建立按鈕區()
        self._建立狀態列()

    # ---------- UI 建立 ----------

    def _建立搜尋區(self):
        框 = ttk.Frame(self.root, padding=10)
        框.pack(fill="x")

        ttk.Label(框, text="歌名：", font=字型).grid(row=0, column=0, sticky="w")
        self.歌名輸入 = ttk.Entry(框, font=字型, width=25)
        self.歌名輸入.grid(row=0, column=1, padx=5)
        self.歌名輸入.bind("<Return>", lambda e: self.執行搜尋())

        ttk.Label(框, text="歌手（選填）：", font=字型).grid(row=0, column=2, sticky="w")
        self.歌手輸入 = ttk.Entry(框, font=字型, width=18)
        self.歌手輸入.grid(row=0, column=3, padx=5)
        self.歌手輸入.bind("<Return>", lambda e: self.執行搜尋())

        ttk.Button(框, text="搜尋", command=self.執行搜尋).grid(row=0, column=4, padx=5)

    def _建立結果區(self):
        框 = ttk.Frame(self.root, padding=(10, 0))
        框.pack(fill="x")

        ttk.Label(框, text="搜尋結果（雙擊載入歌詞）：", font=字型).pack(anchor="w")

        self.結果表 = ttk.Treeview(
            框, columns=("歌名", "歌手"), show="headings", height=6
        )
        self.結果表.heading("歌名", text="歌名")
        self.結果表.heading("歌手", text="歌手")
        self.結果表.column("歌名", width=420)
        self.結果表.column("歌手", width=260)
        self.結果表.pack(side="left", fill="x", expand=True)
        self.結果表.bind("<Double-1>", lambda e: self.載入選取的歌詞())

        捲軸 = ttk.Scrollbar(框, orient="vertical", command=self.結果表.yview)
        self.結果表.configure(yscrollcommand=捲軸.set)
        捲軸.pack(side="left", fill="y")

    def _建立歌詞區(self):
        框 = ttk.Frame(self.root, padding=10)
        框.pack(fill="both", expand=True)

        ttk.Label(框, text="原文歌詞：", font=字型).pack(anchor="w")
        self.原文文字框 = scrolledtext.ScrolledText(框, font=字型, height=10, wrap="word")
        self.原文文字框.pack(fill="both", expand=True)

        ttk.Label(框, text="中文翻譯（每行對應原文每一行）：", font=字型).pack(
            anchor="w", pady=(8, 0)
        )
        self.翻譯文字框 = scrolledtext.ScrolledText(框, font=字型, height=10, wrap="word")
        self.翻譯文字框.pack(fill="both", expand=True)

    def _建立按鈕區(self):
        框 = ttk.Frame(self.root, padding=10)
        框.pack(fill="x")

        ttk.Button(框, text="複製原文", command=self.複製原文).pack(side="left", padx=5)
        ttk.Button(框, text="匯出成 .txt", command=self.匯出檔案).pack(side="left", padx=5)

    def _建立狀態列(self):
        self.狀態文字 = tk.StringVar(value="請輸入歌名開始搜尋")
        ttk.Label(self.root, textvariable=self.狀態文字, padding=5, foreground="#555").pack(
            fill="x", side="bottom"
        )

    # ---------- 事件處理 ----------

    def 執行搜尋(self):
        歌名 = self.歌名輸入.get().strip()
        if not 歌名:
            messagebox.showwarning("提醒", "請先輸入歌名")
            return

        歌手 = self.歌手輸入.get().strip()
        self.狀態文字.set("搜尋中...")
        self.root.update_idletasks()

        try:
            self.搜尋結果 = 搜尋歌曲(歌名, 歌手)
        except requests.RequestException as 錯誤:
            messagebox.showerror("搜尋失敗", f"連線發生問題：{錯誤}")
            self.狀態文字.set("搜尋失敗")
            return

        self.結果表.delete(*self.結果表.get_children())
        for 索引, (標題, 歌手名, _連結) in enumerate(self.搜尋結果):
            self.結果表.insert("", "end", iid=str(索引), values=(標題, 歌手名))

        if not self.搜尋結果:
            self.狀態文字.set("找不到符合的歌曲，換個關鍵字試試")
        else:
            self.狀態文字.set(f"找到 {len(self.搜尋結果)} 筆結果，雙擊載入歌詞")

    def 載入選取的歌詞(self):
        選取項目 = self.結果表.selection()
        if not 選取項目:
            return

        索引 = int(選取項目[0])
        標題, 歌手名, 連結 = self.搜尋結果[索引]

        self.狀態文字.set(f"載入「{標題}」歌詞中...")
        self.root.update_idletasks()

        try:
            標題, 歌手名, 歌詞文字 = 抓取歌詞(連結)
        except (requests.RequestException, ValueError) as 錯誤:
            messagebox.showerror("載入失敗", f"無法取得歌詞：{錯誤}")
            self.狀態文字.set("載入失敗")
            return

        self.目前歌名 = 標題
        self.目前歌手 = 歌手名

        self.原文文字框.delete("1.0", "end")
        self.原文文字框.insert("1.0", 歌詞文字)
        self.翻譯文字框.delete("1.0", "end")

        self.狀態文字.set(f"已載入《{標題}》- {歌手名}，可按「複製原文」拿去翻譯")

    def 複製原文(self):
        原文 = self.原文文字框.get("1.0", "end").strip("\n")
        if not 原文:
            messagebox.showinfo("提醒", "還沒有載入任何歌詞")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(原文)
        self.狀態文字.set("已複製原文歌詞到剪貼簿")

    def 匯出檔案(self):
        原文 = self.原文文字框.get("1.0", "end").strip("\n")
        if not 原文:
            messagebox.showinfo("提醒", "還沒有載入任何歌詞，無法匯出")
            return

        翻譯 = self.翻譯文字框.get("1.0", "end").strip("\n")
        原文行 = 原文.split("\n")
        翻譯行 = 翻譯.split("\n") if 翻譯 else []

        預設檔名 = f"{self.目前歌名 or '歌詞'}_{self.目前歌手 or ''}.txt".strip("_")
        儲存路徑 = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=預設檔名,
            filetypes=[("純文字檔", "*.txt")],
        )
        if not 儲存路徑:
            return

        with open(儲存路徑, "w", encoding="utf-8") as 檔案:
            檔案.write(f"《{self.目前歌名}》- {self.目前歌手}\n")
            檔案.write("=" * 40 + "\n\n")
            for 行號, 原文句 in enumerate(原文行):
                檔案.write(原文句 + "\n")
                if 行號 < len(翻譯行) and 翻譯行[行號]:
                    檔案.write(翻譯行[行號] + "\n")
                檔案.write("\n" if 原文句 == "" else "")

        self.狀態文字.set(f"已匯出到 {儲存路徑}")
        messagebox.showinfo("匯出完成", f"已儲存到：\n{儲存路徑}")


if __name__ == "__main__":
    root = tk.Tk()
    歌曲查詢視窗(root)
    root.mainloop()
