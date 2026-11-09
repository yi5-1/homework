import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import cv2
import numpy as np

import tf_keras as keras
load_model = keras.models.load_model

# 以腳本所在目錄為基準，避免在不同目錄執行時找不到模型
os.chdir(os.path.dirname(os.path.abspath(__file__)))
模型 = load_model("keras_model.h5", compile=False)
class_names = ["剪刀", "石頭", "布", "背景"]

def 辨識手勢(frame):
    img = cv2.resize(frame, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = np.asarray(img, dtype=np.float32).reshape(1, 224, 224, 3)
    img = img / 255.0
    預測 = 模型.predict(img, verbose=0)
    索引 = np.argmax(預測)
    信心 = 預測[0][索引]
    if 索引 == 3 or 信心 < 0.7:
        return "無"
    return class_names[索引]

def 誰贏(a, b):
    if a == b:
        return "平手"
    if (a == "石頭" and b == "剪刀") or \
       (a == "剪刀" and b == "布") or \
       (a == "布" and b == "石頭"):
        return "玩家 1 贏"
    return "玩家 2 贏"

cap1 = cv2.VideoCapture(5, cv2.CAP_DSHOW)
cap2 = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not cap1.isOpened() or not cap2.isOpened():
    print("無法開啟雙鏡頭，請確認兩台攝影機都已連接")
    exit()

cap1.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap1.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

玩家1手勢 = "等待中"
玩家2手勢 = "等待中"
結果文字 = ""
倒數 = -1
倒數計時 = 0
遊戲鎖定 = False
遊戲開始 = False

print("=== 雙鏡頭剪刀石頭布（Keras 模型）===")
print("按 SPACE 開始對戰，按 Q 離開")

while True:
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()
    if not ret1 or not ret2:
        print("無法讀取鏡頭畫面")
        break

    frame1 = cv2.flip(frame1, 1)
    frame2 = cv2.flip(frame2, 1)

    目前手勢1 = 辨識手勢(frame1)
    目前手勢2 = 辨識手勢(frame2)

    if 遊戲開始 and not 遊戲鎖定 and 目前手勢1 != "無" and 目前手勢2 != "無":
        if 倒數 == -1:
            倒數 = 3
            倒數計時 = cv2.getTickCount()

    if 倒數 > 0:
        elapsed = (cv2.getTickCount() - 倒數計時) / cv2.getTickFrequency()
        if elapsed >= 1.0:
            倒數 -= 1
            倒數計時 = cv2.getTickCount()

    if 倒數 == 0 and not 遊戲鎖定:
        玩家1手勢 = 目前手勢1
        玩家2手勢 = 目前手勢2
        結果文字 = 誰贏(玩家1手勢, 玩家2手勢)
        遊戲鎖定 = True
        倒數 = -1

    h1, w1 = frame1.shape[:2]
    cv2.rectangle(frame1, (0, 0), (w1, 50), (0, 0, 0), -1)
    cv2.putText(frame1, "玩家 1", (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.rectangle(frame1, (0, h1 - 30), (w1, h1), (0, 0, 0), -1)
    if 遊戲鎖定:
        cv2.putText(frame1, f"出: {玩家1手勢}", (10, h1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
    else:
        cv2.putText(frame1, f"辨識: {目前手勢1}", (10, h1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    h2, w2 = frame2.shape[:2]
    cv2.rectangle(frame2, (0, 0), (w2, 50), (0, 0, 0), -1)
    cv2.putText(frame2, "玩家 2", (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.rectangle(frame2, (0, h2 - 30), (w2, h2), (0, 0, 0), -1)
    if 遊戲鎖定:
        cv2.putText(frame2, f"出: {玩家2手勢}", (10, h2 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
    else:
        cv2.putText(frame2, f"辨識: {目前手勢2}", (10, h2 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    combined = np.hstack((frame1, frame2))
    h, w = combined.shape[:2]

    if not 遊戲開始:
        cv2.putText(combined, "按 SPACE 開始對戰",
                    (w // 2 - 160, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    elif 倒數 > 0:
        遮罩 = np.zeros_like(combined)
        cv2.addWeighted(遮罩, 0.8, combined, 0.2, 0, combined)
        cv2.putText(combined, str(倒數),
                    (w // 2 - 30, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 6)
    elif 遊戲鎖定:
        (tw, th), _ = cv2.getTextSize(結果文字, cv2.FONT_HERSHEY_SIMPLEX, 2, 4)
        tx = (w - tw) // 2
        ty = h - 50
        cv2.putText(combined, 結果文字, (tx, ty),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
        (sw, sh), _ = cv2.getTextSize("按 SPACE 再玩一局", cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        cv2.putText(combined, "按 SPACE 再玩一局",
                    ((w - sw) // 2, h // 2 + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 255, 100), 3)

    cv2.imshow("雙鏡頭剪刀石頭布", combined)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):
        玩家1手勢 = "等待中"
        玩家2手勢 = "等待中"
        結果文字 = ""
        倒數 = -1
        倒數計時 = 0
        遊戲鎖定 = False
        遊戲開始 = True

cap1.release()
cap2.release()
cv2.destroyAllWindows()
