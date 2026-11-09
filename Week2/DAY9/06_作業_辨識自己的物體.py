# 06 — 作業：接你自己訓練的 Teachable Machine 模型，做一個有實際用途的應用
#
# TODO 1) 到 Teachable Machine 訓練你自己的模型（見 02 教學）
#         想一個有意義的分類任務，例如：
#           - 口罩：戴 / 沒戴 / 戴錯位置
#           - 姿勢：坐姿正 / 駝背 / 站立
#           - 手勢：剪刀 / 石頭 / 布（拳皇對戰？）
#           - 情緒：微笑 / 皺眉 / 中性
#           - 桌面整齊度：乾淨 / 亂
#
# TODO 2) 匯出 → 把 keras_model.h5 + labels.txt 放到本資料夾
#
# TODO 3) 在下方 [自訂邏輯] 區段加上你的創意應用，例如：
#         - 分類結果變化時發聲（winsound / playsound）
#         - 記錄每次分類到 SQLite（結合 DAY6 web_basics）
#         - 觸發 GPIO / 開燈 / 顯示到別的視窗
#         - 分類是「駝背」超過 5 秒 → 跳警告視窗
#
# TODO 4) 交作業時：附上你的 model + 一段 30 秒的 demo 影片
#
# 需要：pip install tensorflow opencv-python numpy
#
# 本版使用「相機測試.py」裡的 CameraStream（雙攝影機、獨立執行緒讀取），
# 同時對兩支攝影機各自跑辨識，並排顯示在同一個視窗。

import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"   # 必須在 import tensorflow 之前

import time
import cv2
import numpy as np
import tensorflow as tf
from PIL import Image, ImageDraw, ImageFont

from 相機測試 import CameraStream, make_placeholder

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(BASE, "keras_model.h5")
LABELS_PATH = os.path.join(BASE, "labels.txt")

# ====== 中文字型（OpenCV putText 不支援中文，改用 PIL）======
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msjh.ttc",   # Microsoft JhengHei
    "C:/Windows/Fonts/msyh.ttc",   # Microsoft YaHei
    "C:/Windows/Fonts/simhei.ttf",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
if FONT_PATH is None:
    raise RuntimeError("找不到中文字型，請安裝微軟正黑體或改字型路徑")

def 畫中文(img_bgr, text, xy, size, color_bgr):
    """在 OpenCV BGR 影像上畫中文，color 用 BGR"""
    img_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(FONT_PATH, size)
    # PIL 用 RGB，把 BGR 換過來
    draw.text(xy, text, font=font, fill=(color_bgr[2], color_bgr[1], color_bgr[0]))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ====== 讀模型 + labels ======
with open(LABELS_PATH, "r", encoding="utf-8") as f:
    labels = [line.strip().split(" ", 1)[1] for line in f if line.strip()]

model = tf.keras.models.load_model(MODEL_PATH, compile=False)


def 辨識畫面(frame):
    """對單一畫面做前處理 + 推論，回傳 (類別名稱, 信心)"""
    img = cv2.resize(frame, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
    img = (img / 127.5) - 1
    img = np.expand_dims(img, axis=0)

    preds = model.predict(img, verbose=0)[0]
    top_idx = int(np.argmax(preds))
    return labels[top_idx], float(preds[top_idx])


class 攝影機狀態:
    """追蹤單一攝影機上一次的類別和累積秒數"""
    def __init__(self):
        self.上次類別 = None
        self.上次時間 = time.time()
        self.持續秒數 = 0.0

    def 更新(self, 目前類別):
        now = time.time()
        dt = now - self.上次時間
        self.上次時間 = now
        if 目前類別 == self.上次類別:
            self.持續秒數 += dt
        else:
            self.持續秒數 = 0.0
            self.上次類別 = 目前類別


def 處理單支攝影機(frame, 狀態):
    """跑辨識、更新持續秒數、把結果畫到畫面上，回傳畫好的 frame"""
    目前類別, 信心 = 辨識畫面(frame)
    狀態.更新(目前類別)

    # ====== [自訂邏輯] 在這裡加你自己的動作！======
    # 範例：某個類別持續 3 秒以上就印警告
    # if 目前類別 == "駝背" and 狀態.持續秒數 > 3.0:
    #     print(">>> 警告：駝背太久了！")
    #
    # 範例：偵測到特定類別發聲（Windows）
    # if 目前類別 == "剪刀" and 狀態.持續秒數 > 1.0:
    #     import winsound
    #     winsound.Beep(1000, 100)

    frame = 畫中文(frame, f"{目前類別} ({信心*100:.1f}%)",
                   (10, 10), 32, (0, 255, 0))
    frame = 畫中文(frame, f"持續: {狀態.持續秒數:.1f}s",
                   (10, 55), 24, (0, 255, 255))
    return frame


# ===== 這裡設定兩支攝影機的來源（同「相機測試.py」）=====
source1 = 1
source2 = 2
# ==========================================================

try:
    cam1 = CameraStream(source1, name="Camera 1")
except RuntimeError as e:
    print(e)
    raise SystemExit(1)

try:
    cam2 = CameraStream(source2, name="Camera 2")
except RuntimeError as e:
    print(e)
    cam1.release()
    raise SystemExit(1)

狀態1 = 攝影機狀態()
狀態2 = 攝影機狀態()

print("按下 'q' 鍵結束程式")

try:
    while True:
        ret1, frame1 = cam1.read()
        ret2, frame2 = cam2.read()

        if not ret1 or frame1 is None:
            frame1 = make_placeholder(text="Camera 1: No Signal")
        else:
            frame1 = 處理單支攝影機(frame1, 狀態1)

        if not ret2 or frame2 is None:
            frame2 = make_placeholder(text="Camera 2: No Signal")
        else:
            frame2 = 處理單支攝影機(frame2, 狀態2)

        # 統一高度以便並排顯示
        h = min(frame1.shape[0], frame2.shape[0])
        frame1_resized = cv2.resize(frame1, (int(frame1.shape[1] * h / frame1.shape[0]), h))
        frame2_resized = cv2.resize(frame2, (int(frame2.shape[1] * h / frame2.shape[0]), h))

        combined = cv2.hconcat([frame1_resized, frame2_resized])
        cv2.imshow("雙攝影機 - 我的分類器應用", combined)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cam1.release()
    cam2.release()
    cv2.destroyAllWindows()
