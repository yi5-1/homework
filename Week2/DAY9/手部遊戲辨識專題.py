import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"   # 必須在 import tensorflow 之前

import math
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


def 畫中文(img_bgr, text, xy, size, color_bgr, 外框顏色=(0, 0, 0), 外框寬度=2):
    """在 OpenCV BGR 影像上畫中文，color 用 BGR；預設加黑色外框讓文字在任何背景下都清晰可讀"""
    img_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(FONT_PATH, size)
    fill = (color_bgr[2], color_bgr[1], color_bgr[0])
    stroke_fill = (外框顏色[2], 外框顏色[1], 外框顏色[0])
    draw.text(xy, text, font=font, fill=fill, stroke_width=外框寬度, stroke_fill=stroke_fill)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def 文字置中座標(text, size, frame_w, frame_h, y偏移=0):
    """算出讓文字在畫面（或某個區域）水平置中、垂直置中於 y偏移 附近的左上角座標"""
    font = ImageFont.truetype(FONT_PATH, size)
    left, top, right, bottom = font.getbbox(text)
    w, h = right - left, bottom - top
    x = (frame_w - w) // 2 - left
    y = (frame_h - h) // 2 - top + y偏移
    return (x, y)


def 半透明底色(img_bgr, pt1, pt2, color_bgr=(0, 0, 0), alpha=0.45):
    """疊一層半透明色塊，讓其上的文字不受攝影機背景干擾"""
    overlay = img_bgr.copy()
    cv2.rectangle(overlay, pt1, pt2, color_bgr, -1, cv2.LINE_AA)
    return cv2.addWeighted(overlay, alpha, img_bgr, 1 - alpha, 0)


def 畫狀態邊框(img_bgr, color_bgr, thickness=10):
    """依目前狀態（等待/倒數/勝負）用不同顏色的外框包住畫面，強化狀態辨識度"""
    out = img_bgr.copy()
    h, w = out.shape[:2]
    cv2.rectangle(out, (0, 0), (w - 1, h - 1), color_bgr, thickness, cv2.LINE_AA)
    return out


# ====== 讀模型 + labels ======
with open(LABELS_PATH, "r", encoding="utf-8") as f:
    labels = [line.strip().split(" ", 1)[1] for line in f if line.strip()]

model = tf.keras.models.load_model(MODEL_PATH, compile=False)

手勢清單 = ("剪刀", "石頭", "布")                       # 排除「背景」
克制關係 = {"剪刀": "布", "石頭": "剪刀", "布": "石頭"}   # key 克制 value


def 取得模型輸入(frame):
    """對單一畫面做前處理，回傳 (實際送進模型的裁切縮圖BGR, 正規化後的模型輸入陣列)
    縮圖可直接疊到畫面上做除錯用，方便確認模型「看到」的到底是不是手"""
    h, w = frame.shape[:2]
    # 先置中裁切成正方形，避免非等比例縮放把手勢壓扁變形
    # （Teachable Machine 網頁版 webcam 訓練時就是用置中正方形畫面）
    side = min(h, w)
    y0 = (h - side) // 2
    x0 = (w - side) // 2
    裁切 = frame[y0:y0 + side, x0:x0 + side]

    縮圖 = cv2.resize(裁切, (224, 224))
    img = cv2.cvtColor(縮圖, cv2.COLOR_BGR2RGB).astype(np.float32)
    img = (img / 127.5) - 1
    img = np.expand_dims(img, axis=0)
    return 縮圖, img


def 辨識手勢(frame):
    """對單一畫面做前處理 + 推論，回傳 (類別名稱, 信心)"""
    _, img = 取得模型輸入(frame)
    preds = model.predict(img, verbose=0)[0]
    top_idx = int(np.argmax(preds))
    return labels[top_idx], float(preds[top_idx])


def 疊上除錯縮圖(disp, 縮圖, preds, xy=(10, 56)):
    """在畫面角落疊上模型實際看到的裁切縮圖 + 每一類的機率（由高到低），
    用來排查「為什麼一直判成同一個」— 只看 top-1 常常看不出來模型其實有把
    正確類別排第二高，列出全部機率才看得出這是誤判還是訓練資料本身有問題"""
    x, y = xy
    大小 = 110
    縮圖顯示 = cv2.resize(縮圖, (大小, 大小))
    cv2.rectangle(disp, (x - 2, y - 2), (x + 大小 + 2, y + 大小 + 2), (0, 255, 255), 2)
    disp[y:y + 大小, x:x + 大小] = 縮圖顯示
    順序 = np.argsort(preds)[::-1]
    for i, idx in enumerate(順序):
        顏色 = (0, 255, 0) if i == 0 else (0, 255, 255)
        文字 = f"{labels[idx]} {preds[idx] * 100:.0f}%"
        disp = 畫中文(disp, 文字, (x, y + 大小 + 4 + i * 22), 18, 顏色)
    return disp


def 判斷勝負(手勢1, 手勢2):
    """回傳 (玩家1的結果文字, 玩家2的結果文字)，各自顯示在自己那半邊畫面"""
    if 手勢1 not in 手勢清單 or 手勢2 not in 手勢清單:
        return "無效回合", "無效回合"
    if 手勢1 == 手勢2:
        return "平手", "平手"
    if 克制關係[手勢1] == 手勢2:
        return "勝利！", "失敗"
    return "失敗", "勝利！"


# ===== 攝影機來源（同「相機測試.py」）=====
source1 = 1
source2 = 5
# ==========================================

try:
    cam1 = CameraStream(source1, name="玩家1")
except RuntimeError as e:
    print(e)
    raise SystemExit(1)

try:
    cam2 = CameraStream(source2, name="玩家2")
except RuntimeError as e:
    print(e)
    cam1.release()
    raise SystemExit(1)

print(f"[診斷] 玩家1鏡頭實際解析度: "
      f"{int(cam1.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cam1.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
print(f"[診斷] 玩家2鏡頭實際解析度: "
      f"{int(cam2.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cam2.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")

倒數秒數   = 3.0
結果停留秒數 = 3.0

狀態     = "等待中"   # 等待中 / 倒數中 / 顯示結果
狀態時間   = time.time()
玩家1手勢  = ""
玩家2手勢  = ""
玩家1結果  = ""
玩家2結果  = ""
除錯模式   = False   # 按 d 切換，開啟後會即時顯示模型實際看到的裁切縮圖與信心，方便排查誤判

print("按空白鍵開始倒數猜拳，按 d 切換除錯縮圖，按 q 離開")

try:
    while True:
        ret1, frame1 = cam1.read()
        ret2, frame2 = cam2.read()

        if not ret1 or frame1 is None:
            frame1 = make_placeholder(text="Camera 1: No Signal")
        if not ret2 or frame2 is None:
            frame2 = make_placeholder(text="Camera 2: No Signal")

        # 顯示用的畫面另外複製一份，避免疊字影響辨識用的原始畫面
        disp1 = frame1.copy()
        disp2 = frame2.copy()

        now = time.time()
        經過秒數 = now - 狀態時間

        邊框顏色 = (150, 150, 150)   # 灰：等待中的預設邊框色

        if 狀態 == "等待中":
            disp1 = 半透明底色(disp1, (0, 0), (disp1.shape[1], 46))
            disp2 = 半透明底色(disp2, (0, 0), (disp2.shape[1], 46))
            disp1 = 畫中文(disp1, "按空白鍵開始", (12, 8), 28, (0, 255, 255))
            disp2 = 畫中文(disp2, "按空白鍵開始", (12, 8), 28, (0, 255, 255))

        elif 狀態 == "倒數中":
            邊框顏色 = (0, 140, 255)  # 橙：倒數中

            剩餘 = 倒數秒數 - 經過秒數
            文字 = str(math.ceil(剩餘)) if 剩餘 > 0 else "出拳！"
            數字顏色 = (0, 0, 255) if 剩餘 > 0 else (0, 255, 0)

            # 倒數中把整個畫面蓋上半透明遮罩，避免兩位玩家提前看到彼此的手勢
            disp1 = 半透明底色(disp1, (0, 0), (disp1.shape[1], disp1.shape[0]), alpha=0.85)
            disp2 = 半透明底色(disp2, (0, 0), (disp2.shape[1], disp2.shape[0]), alpha=0.85)
            xy1 = 文字置中座標(文字, 72, disp1.shape[1], disp1.shape[0])
            xy2 = 文字置中座標(文字, 72, disp2.shape[1], disp2.shape[0])
            disp1 = 畫中文(disp1, 文字, xy1, 72, 數字顏色)
            disp2 = 畫中文(disp2, 文字, xy2, 72, 數字顏色)

            if 剩餘 <= 0:
                # 倒數結束的瞬間，用「還沒疊字」的原始畫面辨識雙方手勢
                玩家1手勢, _ = 辨識手勢(frame1)
                玩家2手勢, _ = 辨識手勢(frame2)
                玩家1結果, 玩家2結果 = 判斷勝負(玩家1手勢, 玩家2手勢)
                狀態 = "顯示結果"
                狀態時間 = now

        elif 狀態 == "顯示結果":
            # 每個玩家自己的勝負結果顏色：勝利綠色、失敗紅色、平手/無效黃色
            顏色對照 = {"勝利！": (0, 255, 0), "失敗": (0, 0, 255)}
            邊框對照 = {"勝利！": (0, 220, 0), "失敗": (0, 0, 220)}
            邊框顏色1 = 邊框對照.get(玩家1結果, (0, 210, 210))
            邊框顏色2 = 邊框對照.get(玩家2結果, (0, 210, 210))

            disp1 = 半透明底色(disp1, (0, 0), (disp1.shape[1], 92))
            disp2 = 半透明底色(disp2, (0, 0), (disp2.shape[1], 92))
            disp1 = 畫中文(disp1, f"玩家1：{玩家1手勢}", (12, 8), 32, (0, 255, 0))
            disp2 = 畫中文(disp2, f"玩家2：{玩家2手勢}", (12, 8), 32, (0, 255, 0))
            disp1 = 畫中文(disp1, 玩家1結果, (12, 46), 40, 顏色對照.get(玩家1結果, (0, 255, 255)))
            disp2 = 畫中文(disp2, 玩家2結果, (12, 46), 40, 顏色對照.get(玩家2結果, (0, 255, 255)))
            disp1 = 畫狀態邊框(disp1, 邊框顏色1)
            disp2 = 畫狀態邊框(disp2, 邊框顏色2)

            if 經過秒數 > 結果停留秒數:
                狀態 = "等待中"
                狀態時間 = now

        if 狀態 != "顯示結果":
            disp1 = 畫狀態邊框(disp1, 邊框顏色)
            disp2 = 畫狀態邊框(disp2, 邊框顏色)

        if 除錯模式:
            縮圖1, img1 = 取得模型輸入(frame1)
            縮圖2, img2 = 取得模型輸入(frame2)
            preds1 = model.predict(img1, verbose=0)[0]
            preds2 = model.predict(img2, verbose=0)[0]
            disp1 = 疊上除錯縮圖(disp1, 縮圖1, preds1)
            disp2 = 疊上除錯縮圖(disp2, 縮圖2, preds2)

        # 統一高度以便並排顯示
        h = min(disp1.shape[0], disp2.shape[0])
        disp1_resized = cv2.resize(disp1, (int(disp1.shape[1] * h / disp1.shape[0]), h))
        disp2_resized = cv2.resize(disp2, (int(disp2.shape[1] * h / disp2.shape[0]), h))

        # 中間分隔線，讓雙畫面在同一個視窗裡也能清楚分開
        分隔線 = np.full((h, 4, 3), (90, 90, 90), dtype=np.uint8)
        combined = cv2.hconcat([disp1_resized, 分隔線, disp2_resized])

        # 頂部標題列
        title_h = 40
        title_bar = np.zeros((title_h, combined.shape[1], 3), dtype=np.uint8)
        title_bar = 畫中文(title_bar, "雙鏡頭猜拳對戰", 文字置中座標("雙鏡頭猜拳對戰", 24, combined.shape[1], title_h), 24, (255, 255, 255))
        combined = cv2.vconcat([title_bar, combined])

        cv2.imshow("手部遊戲辨識專題 - 雙鏡頭猜拳", combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("d"):
            除錯模式 = not 除錯模式
        if key == ord(" ") and 狀態 == "等待中":
            狀態 = "倒數中"
            狀態時間 = now

finally:
    cam1.release()
    cam2.release()
    cv2.destroyAllWindows()
