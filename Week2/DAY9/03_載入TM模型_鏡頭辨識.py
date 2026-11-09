# 03 — 載入 Teachable Machine 匯出的模型，接上 webcam 做即時分類
#
# 前置作業：
# 1) 到 https://teachablemachine.withgoogle.com/ 訓練你的模型（見 02 教學）
# 2) Export → Tensorflow → Keras → 下載 .zip → 解壓縮
# 3) 把 keras_model.h5 和 labels.txt 放到跟這支程式同一個資料夾
#
# 需要：pip install tensorflow opencv-python numpy

import os
# 必須在 import tensorflow 之前設定：讓 TF 2.16+ 也能吃 TM 匯出的舊格式 h5
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import cv2
import numpy as np
import tensorflow as tf
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(BASE, "keras_model.h5")
LABELS_PATH = os.path.join(BASE, "labels.txt")

# ====== 中文字型（OpenCV putText 不支援中文，改用 PIL）======
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msjh.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
if FONT_PATH is None:
    raise RuntimeError("找不到中文字型")

def 畫中文(img_bgr, text, xy, size, color_bgr):
    img_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(FONT_PATH, size)
    draw.text(xy, text, font=font, fill=(color_bgr[2], color_bgr[1], color_bgr[0]))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ====== 讀 labels ======
# TM 的 labels.txt 每一行格式：'0 類別名稱'
with open(LABELS_PATH, "r", encoding="utf-8") as f:
    labels = [line.strip().split(" ", 1)[1] for line in f if line.strip()]
print(f"讀到 {len(labels)} 個類別：{labels}")

# ====== 讀模型 ======
# compile=False 表示只要拿來推論，不需要 loss / optimizer
model = tf.keras.models.load_model(MODEL_PATH, compile=False)
print("模型載入成功，輸入大小：", model.input_shape)

# ====== 開 webcam ======
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("無法開啟 webcam")

print("按 q 離開")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # ====== 預處理：TM 的模型固定要 224x224、RGB、[-1, 1] 正規化 ======
    img = cv2.resize(frame, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
    img = (img / 127.5) - 1                # normalize 到 [-1, 1]
    img = np.expand_dims(img, axis=0)      # 加上 batch 維度 → (1, 224, 224, 3)

    # ====== 推論 ======
    preds = model.predict(img, verbose=0)[0]   # shape = (類別數,)
    top_idx = int(np.argmax(preds))
    top_label = labels[top_idx]
    top_conf  = float(preds[top_idx])

    # ====== 畫在鏡頭畫面上（中文用 PIL）======
    frame = 畫中文(frame, f"{top_label}  {top_conf*100:.1f}%",
                   (10, 10), 32, (0, 255, 0))

    # 底下：每一類的機率長條圖
    for i, (name, prob) in enumerate(zip(labels, preds)):
        y = 70 + i * 30
        bar_w = int(prob * 300)
        cv2.rectangle(frame, (10, y), (10 + bar_w, y + 22), (0, 200, 255), -1)
        frame = 畫中文(frame, f"{name}: {prob*100:5.1f}%",
                       (320, y - 2), 20, (0, 0, 0))

    cv2.imshow("Teachable Machine 分類", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
