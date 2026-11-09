# 07 — 手寫辨識 GUI：用滑鼠在 tkinter 畫布上寫數字，CNN 即時預測
#
# 整合 DAY4 的 tkinter Canvas 跟 04 的 MNIST CNN。
# 執行流程：
#   1) 若本地沒有 mnist_cnn.h5，先訓練一次（3 epochs，CPU 約 1~2 分鐘）
#   2) 開視窗：左邊 280x280 畫布（放大 10 倍好畫），右邊即時機率長條
#   3) 放開滑鼠自動預測；「清空」按鈕重畫

import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"   # 必須在 import tensorflow 之前

from pathlib import Path
import numpy as np
import tkinter as tk
import tensorflow as tf
from PIL import Image, ImageDraw

BASE = Path(__file__).parent
MODEL_PATH = BASE / "mnist_cnn.h5"


# ====== 訓練 or 載入 MNIST CNN ======
def 準備模型():
    if MODEL_PATH.exists():
        print(f"載入既有模型 {MODEL_PATH}")
        return tf.keras.models.load_model(MODEL_PATH, compile=False)

    print("找不到訓練好的模型，開始訓練（第一次會慢一點，之後就秒開）...")
    (x_train, y_train), _ = tf.keras.datasets.mnist.load_data()
    x_train = (x_train.astype("float32") / 255.0)[..., None]

    model = tf.keras.Sequential([
        tf.keras.Input((28, 28, 1)),
        tf.keras.layers.Conv2D(16, 3, activation="relu"),
        tf.keras.layers.MaxPool2D(),
        tf.keras.layers.Conv2D(32, 3, activation="relu"),
        tf.keras.layers.MaxPool2D(),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(10, activation="softmax"),
    ])
    model.compile(optimizer="adam",
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    model.fit(x_train, y_train, epochs=3, batch_size=128, validation_split=0.1, verbose=1)
    model.save(MODEL_PATH)
    print(f"訓練完成，模型存到 {MODEL_PATH}")
    return model


# ====== 把使用者畫的圖處理成 MNIST 訓練集的樣子（置中 + 大小相近）======
def 前處理(pil_img):
    """
    MNIST 數字是白色描邊在黑背景，且已置中、大小約 20x20 塞在 28x28 中央。
    使用者亂畫的可能偏一邊或太小，我們裁切 + 縮放 + 置中，準確率會大幅提升。
    """
    arr = np.array(pil_img)
    有畫的列 = np.any(arr > 0, axis=1)
    有畫的行 = np.any(arr > 0, axis=0)
    if not 有畫的列.any():
        return None    # 空白畫布

    rmin, rmax = np.where(有畫的列)[0][[0, -1]]
    cmin, cmax = np.where(有畫的行)[0][[0, -1]]
    裁切 = Image.fromarray(arr[rmin:rmax + 1, cmin:cmax + 1])

    # 等比例縮到 20x20 內
    裁切.thumbnail((20, 20), Image.LANCZOS)

    # 貼到 28x28 的正中央
    out = Image.new("L", (28, 28), 0)
    out.paste(裁切, ((28 - 裁切.width) // 2, (28 - 裁切.height) // 2))
    return out


class 手寫辨識App:
    畫布大小 = 280   # 10 倍放大好畫
    筆寬     = 14

    def __init__(self):
        self.model = 準備模型()

        self.root = tk.Tk()
        self.root.title("MNIST 手寫數字辨識")

        # ====== 左邊：畫布 ======
        left = tk.Frame(self.root)
        left.pack(side="left", padx=12, pady=12)

        tk.Label(left, text="用滑鼠拖曳畫一個數字 (0~9)",
                 font=("Microsoft JhengHei", 12)).pack()

        self.canvas = tk.Canvas(left, width=self.畫布大小, height=self.畫布大小,
                                 bg="black", cursor="pencil")
        self.canvas.pack()

        # PIL 影像同步：canvas 只是給人看，真正拿去預測的是這張
        self._重置PIL()

        self.canvas.bind("<Button-1>",         self._開始畫)
        self.canvas.bind("<B1-Motion>",        self._畫線)
        self.canvas.bind("<ButtonRelease-1>",  lambda e: self.預測())
        self._上一點 = (None, None)

        # ====== 右邊：預測結果 ======
        right = tk.Frame(self.root)
        right.pack(side="left", padx=12, pady=12, fill="y")

        self.結果字串 = tk.StringVar(value="預測: ?")
        tk.Label(right, textvariable=self.結果字串,
                 font=("Microsoft JhengHei", 40, "bold"),
                 fg="#2a5cb5").pack()

        # 10 條機率長條
        self.bar_canvas = tk.Canvas(right, width=310, height=280, bg="white",
                                     highlightthickness=1, highlightbackground="#ccc")
        self.bar_canvas.pack(pady=8)
        self.bars, self.bar_texts = [], []
        for i in range(10):
            y = 8 + i * 27
            self.bar_canvas.create_text(15, y + 10, text=str(i),
                                         font=("Microsoft JhengHei", 14, "bold"))
            bar = self.bar_canvas.create_rectangle(30, y, 30, y + 20,
                                                    fill="#3498db", outline="")
            txt = self.bar_canvas.create_text(305, y + 10, text="0.0%", anchor="e",
                                               font=("Microsoft JhengHei", 10))
            self.bars.append(bar); self.bar_texts.append(txt)

        # 按鈕
        tk.Button(right, text="重新辨識", command=self.預測,
                  font=("Microsoft JhengHei", 12)).pack(fill="x", pady=2)
        tk.Button(right, text="清空", command=self.清空,
                  font=("Microsoft JhengHei", 12)).pack(fill="x", pady=2)

        self.root.mainloop()

    # ---------- 畫布事件 ----------
    def _重置PIL(self):
        self._pil = Image.new("L", (self.畫布大小, self.畫布大小), 0)
        self._draw = ImageDraw.Draw(self._pil)

    def _開始畫(self, e):
        self._上一點 = (e.x, e.y)

    def _畫線(self, e):
        r = self.筆寬
        x0, y0 = self._上一點
        if x0 is not None:
            # 畫在 canvas（螢幕）
            self.canvas.create_line(x0, y0, e.x, e.y, fill="white",
                                     width=r * 2, capstyle="round", smooth=True)
            # 同步畫在 PIL（給模型看的）
            self._draw.line([(x0, y0), (e.x, e.y)], fill=255, width=r * 2)
        # 頭尾補圓，讓 stroke 平滑
        self.canvas.create_oval(e.x - r, e.y - r, e.x + r, e.y + r,
                                 fill="white", outline="")
        self._draw.ellipse((e.x - r, e.y - r, e.x + r, e.y + r), fill=255)
        self._上一點 = (e.x, e.y)

    # ---------- 動作 ----------
    def 清空(self):
        self.canvas.delete("all")
        self._重置PIL()
        self.結果字串.set("預測: ?")
        for i in range(10):
            self.bar_canvas.coords(self.bars[i], 30, 8 + i * 27, 30, 28 + i * 27)
            self.bar_canvas.itemconfig(self.bar_texts[i], text="0.0%")

    def 預測(self):
        img28 = 前處理(self._pil)
        if img28 is None:
            self.結果字串.set("預測: ?")
            return

        arr = np.array(img28).astype("float32") / 255.0
        arr = arr[None, ..., None]                       # (1, 28, 28, 1)

        preds = self.model.predict(arr, verbose=0)[0]
        top = int(np.argmax(preds))
        self.結果字串.set(f"預測: {top}  ({preds[top]*100:.1f}%)")

        # 更新 10 條長條
        for i in range(10):
            w = int(preds[i] * 260)
            self.bar_canvas.coords(self.bars[i], 30, 8 + i * 27, 30 + w, 28 + i * 27)
            self.bar_canvas.itemconfig(self.bar_texts[i], text=f"{preds[i]*100:.1f}%")


if __name__ == "__main__":
    手寫辨識App()
