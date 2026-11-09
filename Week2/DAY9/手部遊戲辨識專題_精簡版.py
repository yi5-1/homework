import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
import math, time, cv2, numpy as np, tensorflow as tf
from PIL import Image, ImageDraw, ImageFont
from 相機測試 import CameraStream, make_placeholder

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "keras_model.h5")
LABELS_PATH = os.path.join(BASE, "labels.txt")

FONT_PATH = next((p for p in ["C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"] if os.path.exists(p)), None)
if FONT_PATH is None:
    raise RuntimeError("找不到中文字型，請安裝微軟正黑體或改字型路徑")


def 畫中文(img, text, xy, size, color, 外框=(0, 0, 0), 寬=2):
    p = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(p)
    f = ImageFont.truetype(FONT_PATH, size)
    d.text(xy, text, font=f, fill=(color[2], color[1], color[0]), stroke_width=寬, stroke_fill=(外框[2], 外框[1], 外框[0]))
    return cv2.cvtColor(np.array(p), cv2.COLOR_RGB2BGR)


def 文字置中座標(text, size, w, h, y偏移=0):
    f = ImageFont.truetype(FONT_PATH, size); l, t, r, b = f.getbbox(text)
    return ((w - (r - l)) // 2 - l, (h - (b - t)) // 2 - t + y偏移)


def 半透明底色(img, p1, p2, color=(0, 0, 0), alpha=0.45):
    o = img.copy(); cv2.rectangle(o, p1, p2, color, -1, cv2.LINE_AA)
    return cv2.addWeighted(o, alpha, img, 1 - alpha, 0)


def 畫狀態邊框(img, color, 寬=10):
    o = img.copy(); h, w = o.shape[:2]; cv2.rectangle(o, (0, 0), (w - 1, h - 1), color, 寬, cv2.LINE_AA); return o


with open(LABELS_PATH, "r", encoding="utf-8") as f:
    labels = [l.strip().split(" ", 1)[1] for l in f if l.strip()]
model = tf.keras.models.load_model(MODEL_PATH, compile=False)

手勢清單 = ("剪刀", "石頭", "布")
克制關係 = {"剪刀": "布", "石頭": "剪刀", "布": "石頭"}


def 取得模型輸入(frame):
    h, w = frame.shape[:2]; s = min(h, w); y0 = (h - s) // 2; x0 = (w - s) // 2
    縮圖 = cv2.resize(frame[y0:y0 + s, x0:x0 + s], (224, 224))
    img = cv2.cvtColor(縮圖, cv2.COLOR_BGR2RGB).astype(np.float32) / 127.5 - 1
    return 縮圖, np.expand_dims(img, axis=0)


def 辨識手勢(frame):
    _, img = 取得模型輸入(frame); preds = model.predict(img, verbose=0)[0]; i = int(np.argmax(preds))
    return labels[i], float(preds[i])


def 疊上除錯縮圖(disp, 縮圖, preds, xy=(10, 56)):
    x, y = xy; 大小 = 110; t = cv2.resize(縮圖, (大小, 大小))
    cv2.rectangle(disp, (x - 2, y - 2), (x + 大小 + 2, y + 大小 + 2), (0, 255, 255), 2)
    disp[y:y + 大小, x:x + 大小] = t
    for i, idx in enumerate(np.argsort(preds)[::-1]):
        c = (0, 255, 0) if i == 0 else (0, 255, 255)
        disp = 畫中文(disp, f"{labels[idx]} {preds[idx] * 100:.0f}%", (x, y + 大小 + 4 + i * 22), 18, c)
    return disp


def 判斷勝負(a, b):
    if a not in 手勢清單 or b not in 手勢清單:
        return "無效回合", "無效回合"
    if a == b:
        return "平手", "平手"
    return ("勝利！", "失敗") if 克制關係[a] == b else ("失敗", "勝利！")


source1, source2 = 1, 5

try:
    cam1 = CameraStream(source1, name="玩家1")
except RuntimeError as e:
    print(e); raise SystemExit(1)
try:
    cam2 = CameraStream(source2, name="玩家2")
except RuntimeError as e:
    print(e); cam1.release(); raise SystemExit(1)

print(f"[診斷] 玩家1鏡頭實際解析度: {int(cam1.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cam1.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
print(f"[診斷] 玩家2鏡頭實際解析度: {int(cam2.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cam2.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")

倒數秒數, 結果停留秒數 = 3.0, 3.0
狀態, 狀態時間 = "等待中", time.time()
玩家1手勢 = 玩家2手勢 = 玩家1結果 = 玩家2結果 = ""
除錯模式 = False
print("按空白鍵開始倒數猜拳，按 d 切換除錯縮圖，按 q 離開")

try:
    while True:
        ret1, frame1 = cam1.read(); ret2, frame2 = cam2.read()
        if not ret1 or frame1 is None:
            frame1 = make_placeholder(text="Camera 1: No Signal")
        if not ret2 or frame2 is None:
            frame2 = make_placeholder(text="Camera 2: No Signal")
        disp1, disp2 = frame1.copy(), frame2.copy()
        now = time.time(); 經過秒數 = now - 狀態時間
        邊框顏色 = (150, 150, 150)

        if 狀態 == "等待中":
            disp1 = 半透明底色(disp1, (0, 0), (disp1.shape[1], 46)); disp2 = 半透明底色(disp2, (0, 0), (disp2.shape[1], 46))
            disp1 = 畫中文(disp1, "按空白鍵開始", (12, 8), 28, (0, 255, 255)); disp2 = 畫中文(disp2, "按空白鍵開始", (12, 8), 28, (0, 255, 255))

        elif 狀態 == "倒數中":
            邊框顏色 = (0, 140, 255)
            剩餘 = 倒數秒數 - 經過秒數
            文字 = "出拳！" if 剩餘 <= 0 else str(math.ceil(剩餘))
            數字顏色 = (0, 255, 0) if 剩餘 <= 0 else (0, 0, 255)
            disp1 = 半透明底色(disp1, (0, 0), (disp1.shape[1], disp1.shape[0]), alpha=0.85)
            disp2 = 半透明底色(disp2, (0, 0), (disp2.shape[1], disp2.shape[0]), alpha=0.85)
            disp1 = 畫中文(disp1, 文字, 文字置中座標(文字, 72, disp1.shape[1], disp1.shape[0]), 72, 數字顏色)
            disp2 = 畫中文(disp2, 文字, 文字置中座標(文字, 72, disp2.shape[1], disp2.shape[0]), 72, 數字顏色)
            if 剩餘 <= 0:
                玩家1手勢, _ = 辨識手勢(frame1); 玩家2手勢, _ = 辨識手勢(frame2)
                玩家1結果, 玩家2結果 = 判斷勝負(玩家1手勢, 玩家2手勢)
                狀態, 狀態時間 = "顯示結果", now

        elif 狀態 == "顯示結果":
            顏色對照 = {"勝利！": (0, 255, 0), "失敗": (0, 0, 255)}
            邊框對照 = {"勝利！": (0, 220, 0), "失敗": (0, 0, 220)}
            邊框顏色1 = 邊框對照.get(玩家1結果, (0, 210, 210)); 邊框顏色2 = 邊框對照.get(玩家2結果, (0, 210, 210))
            disp1 = 半透明底色(disp1, (0, 0), (disp1.shape[1], 92)); disp2 = 半透明底色(disp2, (0, 0), (disp2.shape[1], 92))
            disp1 = 畫中文(disp1, f"玩家1：{玩家1手勢}", (12, 8), 32, (0, 255, 0)); disp2 = 畫中文(disp2, f"玩家2：{玩家2手勢}", (12, 8), 32, (0, 255, 0))
            disp1 = 畫中文(disp1, 玩家1結果, (12, 46), 40, 顏色對照.get(玩家1結果, (0, 255, 255)))
            disp2 = 畫中文(disp2, 玩家2結果, (12, 46), 40, 顏色對照.get(玩家2結果, (0, 255, 255)))
            disp1 = 畫狀態邊框(disp1, 邊框顏色1); disp2 = 畫狀態邊框(disp2, 邊框顏色2)
            if 經過秒數 > 結果停留秒數:
                狀態, 狀態時間 = "等待中", now

        if 狀態 != "顯示結果":
            disp1 = 畫狀態邊框(disp1, 邊框顏色); disp2 = 畫狀態邊框(disp2, 邊框顏色)

        if 除錯模式:
            縮圖1, img1 = 取得模型輸入(frame1); 縮圖2, img2 = 取得模型輸入(frame2)
            preds1 = model.predict(img1, verbose=0)[0]; preds2 = model.predict(img2, verbose=0)[0]
            disp1 = 疊上除錯縮圖(disp1, 縮圖1, preds1); disp2 = 疊上除錯縮圖(disp2, 縮圖2, preds2)

        h = min(disp1.shape[0], disp2.shape[0])
        d1 = cv2.resize(disp1, (int(disp1.shape[1] * h / disp1.shape[0]), h))
        d2 = cv2.resize(disp2, (int(disp2.shape[1] * h / disp2.shape[0]), h))
        分隔線 = np.full((h, 4, 3), (90, 90, 90), dtype=np.uint8)
        combined = cv2.hconcat([d1, 分隔線, d2])

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
            狀態, 狀態時間 = "倒數中", now

finally:
    cam1.release(); cam2.release(); cv2.destroyAllWindows()
