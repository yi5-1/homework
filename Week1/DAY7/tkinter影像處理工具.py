# 用 tkinter 做一個「影像處理即時工具」
# 左邊 Canvas 顯示 webcam 畫面（可切換 Raw/Gray/Blur/Canny/Shape）
# 右邊控制面板用 Scale / Checkbutton 調參，比 OpenCV 內建 trackbar 直觀得多
#
# 需要：pip install opencv-python pillow

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk

try:
    from PIL import Image, ImageTk
except ImportError:
    print("需要 Pillow：請先執行  pip install pillow")
    raise


class 影像工具:
    def __init__(self):
        # ====== webcam ======
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("無法開啟 webcam")

        # 讀一張決定 canvas 大小
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("讀不到畫面")
        self.H, self.W = frame.shape[:2]

        # ====== 建立主視窗 ======
        self.root = tk.Tk()
        self.root.title("即時影像處理工具 (tkinter + OpenCV)")
        self.root.protocol("WM_DELETE_WINDOW", self.關閉)

        # 主 layout：左邊 Canvas，右邊控制面板
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=8, pady=8)

        # ====== 左：Canvas 顯示畫面 ======
        left = tk.Frame(main)
        left.pack(side="left", padx=(0, 8))

        self.canvas = tk.Canvas(left, width=self.W, height=self.H, bg="black")
        self.canvas.pack()
        self.canvas_img_id = None
        self.photo = None  # 一定要保留 reference，不然會被 GC 掉

        self.狀態列 = tk.Label(left, text="", anchor="w", fg="#333",
                              font=("Microsoft JhengHei", 10))
        self.狀態列.pack(fill="x", pady=(4, 0))

        # ====== 右：控制面板 ======
        right = tk.Frame(main)
        right.pack(side="left", fill="y")

        self.建立控制面板(right)

        # ====== 開始更新迴圈 ======
        self.更新畫面()

    # -----------------------------------------------------------
    def 建立控制面板(self, parent):
        # 視角切換 (radio button)
        tk.Label(parent, text="視角切換", font=("Microsoft JhengHei", 11, "bold")).pack(anchor="w")
        self.view = tk.IntVar(value=4)
        for i, name in enumerate(["原始 (BGR)", "灰階 (Gray)", "模糊 (Blur)",
                                   "Canny 邊緣", "形狀偵測 (Shape)"]):
            tk.Radiobutton(parent, text=name, variable=self.view, value=i,
                           font=("Microsoft JhengHei", 10)).pack(anchor="w")

        ttk.Separator(parent).pack(fill="x", pady=6)

        # 模糊參數
        tk.Label(parent, text="Gaussian Blur", font=("Microsoft JhengHei", 11, "bold")).pack(anchor="w")
        self.ksize = tk.IntVar(value=7)
        self.sigma = tk.DoubleVar(value=1.5)
        self._slider(parent, "ksize (奇數)", self.ksize, 1, 31, 2)
        self._slider(parent, "sigma", self.sigma, 0.0, 10.0, 0.1, digits=1)

        ttk.Separator(parent).pack(fill="x", pady=6)

        # Canny 參數
        tk.Label(parent, text="Canny 邊緣", font=("Microsoft JhengHei", 11, "bold")).pack(anchor="w")
        self.canny_t1 = tk.IntVar(value=30)
        self.canny_t2 = tk.IntVar(value=150)
        self._slider(parent, "T1 (低門檻)", self.canny_t1, 0, 500, 1)
        self._slider(parent, "T2 (高門檻)", self.canny_t2, 0, 500, 1)

        ttk.Separator(parent).pack(fill="x", pady=6)

        # 形狀偵測參數
        tk.Label(parent, text="形狀偵測條件", font=("Microsoft JhengHei", 11, "bold")).pack(anchor="w")
        self.min_area = tk.IntVar(value=500)
        self.max_area = tk.IntVar(value=50000)
        self.eps_pct  = tk.IntVar(value=4)
        self.circ_thr = tk.IntVar(value=75)
        self._slider(parent, "Min Area",        self.min_area, 0,   30000, 100)
        self._slider(parent, "Max Area",        self.max_area, 100, 200000, 1000)
        self._slider(parent, "Epsilon %",       self.eps_pct,  1,   15,    1)
        self._slider(parent, "Circle Thresh %", self.circ_thr, 0,   100,   1)

        ttk.Separator(parent).pack(fill="x", pady=6)

        # 形狀開關
        tk.Label(parent, text="要顯示哪些形狀", font=("Microsoft JhengHei", 11, "bold")).pack(anchor="w")
        self.show_tri = tk.BooleanVar(value=True)
        self.show_sq  = tk.BooleanVar(value=True)
        self.show_ci  = tk.BooleanVar(value=True)
        self.show_pg  = tk.BooleanVar(value=False)
        for text, var in [("三角形", self.show_tri),
                          ("正方形 / 矩形", self.show_sq),
                          ("圓形", self.show_ci),
                          ("多邊形 5+", self.show_pg)]:
            tk.Checkbutton(parent, text=text, variable=var,
                           font=("Microsoft JhengHei", 10)).pack(anchor="w")

        ttk.Separator(parent).pack(fill="x", pady=6)

        # 按鈕
        tk.Button(parent, text="存圖 snapshot.png", command=self.存圖,
                  font=("Microsoft JhengHei", 10)).pack(fill="x", pady=2)
        tk.Button(parent, text="離開", command=self.關閉,
                  font=("Microsoft JhengHei", 10)).pack(fill="x", pady=2)

    def _slider(self, parent, label, var, mn, mx, step, digits=0):
        """幫忙包一個 label + Scale"""
        row = tk.Frame(parent)
        row.pack(fill="x", pady=1)
        tk.Label(row, text=label, width=14, anchor="w",
                 font=("Microsoft JhengHei", 9)).pack(side="left")
        s = tk.Scale(row, variable=var, from_=mn, to=mx,
                     resolution=step, orient="horizontal", length=170,
                     digits=digits + 1 if isinstance(var, tk.DoubleVar) else 0,
                     showvalue=True)
        s.pack(side="left")

    # -----------------------------------------------------------
    def 處理畫面(self, frame):
        """依當前 view 回傳要顯示的 BGR 影像"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 模糊 ksize 必須奇數
        ksize = max(1, self.ksize.get())
        if ksize % 2 == 0:
            ksize += 1
        blur = cv2.GaussianBlur(gray, (ksize, ksize), self.sigma.get())
        edges = cv2.Canny(blur, self.canny_t1.get(), self.canny_t2.get())

        view = self.view.get()
        if view == 0:
            self.狀態列.config(text="視角：原始 BGR")
            return frame.copy()
        if view == 1:
            self.狀態列.config(text="視角：灰階")
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        if view == 2:
            self.狀態列.config(text=f"視角：模糊  ksize={ksize}  sigma={self.sigma.get():.1f}")
            return cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR)
        if view == 3:
            self.狀態列.config(text=f"視角：Canny  T1={self.canny_t1.get()}  T2={self.canny_t2.get()}")
            return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # view == 4：形狀偵測
        return self.畫形狀(frame.copy(), edges)

    def 畫形狀(self, out, edges):
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        counts = {"Triangle": 0, "Square": 0, "Rectangle": 0, "Circle": 0, "Polygon": 0}

        min_area = self.min_area.get()
        max_area = self.max_area.get()
        eps_pct  = max(self.eps_pct.get(), 1) / 100.0
        circ_thr = self.circ_thr.get() / 100.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue
            perimeter = cv2.arcLength(cnt, True)
            if perimeter <= 0:
                continue

            hull   = cv2.convexHull(cnt)
            approx = cv2.approxPolyDP(hull, eps_pct * cv2.arcLength(hull, True), True)
            vtx    = len(approx)
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            shape, color = None, (255, 255, 255)

            if self.show_ci.get() and circularity > circ_thr and vtx >= 5:
                shape = "Circle"
                color = (0, 0, 255)
                counts["Circle"] += 1
            elif self.show_tri.get() and vtx == 3:
                shape = "Triangle"
                color = (0, 255, 255)
                counts["Triangle"] += 1
            elif self.show_sq.get() and vtx == 4:
                x, y, w, h = cv2.boundingRect(approx)
                ratio = w / float(h) if h > 0 else 0
                if 0.85 <= ratio <= 1.15:
                    shape = "Square"; counts["Square"] += 1
                else:
                    shape = "Rectangle"; counts["Rectangle"] += 1
                color = (0, 255, 0)
            elif self.show_pg.get() and vtx >= 5:
                shape = f"Polygon-{vtx}"
                color = (255, 100, 200)
                counts["Polygon"] += 1

            if shape:
                cv2.drawContours(out, [approx], -1, color, 2)
                cv2.circle(out, (cX, cY), 4, color, -1)
                cv2.putText(out, f"{shape} A:{int(area)}",
                            (cX - 55, cY - 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        # 狀態列顯示計數
        parts = [f"{k}:{v}" for k, v in counts.items() if v > 0]
        self.狀態列.config(text="視角：形狀偵測  |  " + ("  ".join(parts) if parts else "沒偵測到形狀"))
        return out

    # -----------------------------------------------------------
    def 更新畫面(self):
        ret, frame = self.cap.read()
        if ret:
            display = self.處理畫面(frame)
            # OpenCV 是 BGR，PIL 要 RGB
            rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            self.photo = ImageTk.PhotoImage(img)     # 保留 reference！
            if self.canvas_img_id is None:
                self.canvas_img_id = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
            else:
                self.canvas.itemconfig(self.canvas_img_id, image=self.photo)
            self.最後畫面 = display
        # 30 fps
        self.root.after(33, self.更新畫面)

    def 存圖(self):
        if hasattr(self, "最後畫面"):
            cv2.imwrite("snapshot.png", self.最後畫面)
            self.狀態列.config(text="已儲存 snapshot.png")

    def 關閉(self):
        try:
            self.cap.release()
        except Exception:
            pass
        self.root.destroy()

    def 執行(self):
        self.root.mainloop()


if __name__ == "__main__":
    影像工具().執行()
