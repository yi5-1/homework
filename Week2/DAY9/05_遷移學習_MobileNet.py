# 05 — 用預訓練 MobileNetV2 分類 webcam 畫面
#
# 觀念：遷移學習 (Transfer Learning)
#   Google 已經花很多 GPU 在 ImageNet（120 萬張，1000 類）訓練好 MobileNetV2
#   我們直接拿來用 —— 不用重訓就能認出 1000 種常見物體（狗、貓、水果、家電...）
#
# 這就是 Teachable Machine 的底層策略：拿 MobileNet 當「特徵萃取器」，
# 你只重訓最後一層來認你的類別。
#
# 需要：pip install tensorflow opencv-python numpy

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2, preprocess_input, decode_predictions,
)

# ====== 載入 ImageNet 預訓練權重 ======
# 第一次跑會下載約 14MB 權重，之後會 cache 在 ~/.keras/
print("載入預訓練 MobileNetV2 ...")
model = MobileNetV2(weights="imagenet")
print("完成！模型輸入：", model.input_shape)

# ====== 開 webcam ======
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("無法開啟 webcam")

print("按 q 離開；把物體對著鏡頭讓它認")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 預處理：MobileNetV2 要 224x224 RGB，用它自帶的 preprocess_input
    img = cv2.resize(frame, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
    img = preprocess_input(img)
    img = np.expand_dims(img, axis=0)

    # 推論 → 取前 3 名
    preds = model.predict(img, verbose=0)
    top3 = decode_predictions(preds, top=3)[0]
    # top3 = [(imagenet_id, 名字, 機率), ...]

    # 畫到畫面上
    for i, (_, name, score) in enumerate(top3):
        text = f"{i+1}. {name}: {score*100:.1f}%"
        cv2.putText(frame, text, (10, 40 + i * 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("MobileNetV2 (ImageNet 1000 class)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

# ====== 小提示 ======
# 這裡「model.predict」就是「推論」；我們完全沒有 model.fit，
# 因為權重已經是別人訓練好的。
#
# 想要它認你的類別（不在 ImageNet 1000 類裡）怎麼辦？
#   A. 用 Teachable Machine（GUI 遷移學習）
#   B. 自己寫 fine-tune：把 top 拿掉，接自己的 Dense 層，只訓練新加的層
#      → 進階練習可以參考 tf.keras Application 官方教學
