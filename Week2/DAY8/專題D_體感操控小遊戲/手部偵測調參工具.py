# 手部偵測調參工具（獨立小程式，不會動到遊戲本體）
#
# 拖曳滑桿即時調整 YCrCb 膚色範圍 / 最小色塊面積 / 臉部排除。
# 臉部排除跟 hand_tracker.py 用同一套「非破壞式」做法：不會把遮罩裡臉的像素挖掉
# （那樣手舉在臉附近時常常連手都被一起挖掉），而是每個候選色塊都算出來後，
# 只有「重心真的落在紅色臉部框內」才會被標成粉紫色 rejected(face-like) 排除掉，
# 手即使邊緣蹭到紅框也不會被牽連。
#   - 如果臉在畫面裡卻沒有紅框蓋住 → 代表當下角度/光線下 Haar 臉部偵測沒框到臉，
#     這是「一直吃到臉」最常見的原因，跟角度/距離/光線有關，跟滑桿無關。
#
# 用法：
#   python 手部偵測調參工具.py
# 把手放進畫面調到「手是綠色/黃色凸包、臉是粉紫色 rejected」的範圍後，按 q 離開，
# 終端機最後會印出可以直接貼回 hand_tracker.py 的數字。

import cv2
import numpy as np
import os

# OpenCV 的視窗標題/滑桿名稱/cv2.putText 都是走它自己的 GUI 跟 Hershey 字型繪製，
# 不是走 Python 主控台輸出，中文在這幾個地方常常會變亂碼或整個顯示不出來
# （Hershey 字型甚至完全不支援非 ASCII 字元），所以這些一律用英文，
# 其餘變數名/註解/print() 維持中文不受影響。
視窗名 = "Hand Detect Tuner"


def _無操作(x):
    pass


def 開啟攝影機():
    候選後端 = [cv2.CAP_DSHOW, cv2.CAP_ANY] if os.name == "nt" else [cv2.CAP_ANY]
    for backend in 候選後端:
        for idx in range(2):
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                return cap
            cap.release()
    return None


def main():
    cap = 開啟攝影機()
    if cap is None:
        print("[錯誤] 找不到可用的攝影機。")
        return

    cv2.namedWindow(視窗名)
    # 滑桿初始值取自 hand_tracker.py 目前的預設膚色範圍；名稱刻意用英文（見上方說明）
    cv2.createTrackbar("Y_min", 視窗名, 0, 255, _無操作)
    cv2.createTrackbar("Y_max", 視窗名, 255, 255, _無操作)
    cv2.createTrackbar("Cr_min", 視窗名, 133, 255, _無操作)
    cv2.createTrackbar("Cr_max", 視窗名, 173, 255, _無操作)
    cv2.createTrackbar("Cb_min", 視窗名, 77, 255, _無操作)
    cv2.createTrackbar("Cb_max", 視窗名, 127, 255, _無操作)
    cv2.createTrackbar("MinArea_x100", 視窗名, 15, 100, _無操作)
    cv2.createTrackbar("ExcludeFace", 視窗名, 1, 1, _無操作)
    cv2.createTrackbar("FacePad_pct", 視窗名, 40, 100, _無操作)

    臉部偵測器 = cv2.CascadeClassifier(
        os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    )

    print("拖曳滑桿調整範圍，按 q 離開；數值變動時會印在終端機。")
    上次列印 = None

    for _ in range(10):  # 暖幀，跟遊戲本體一樣避免第一張全黑/曝光沒調好
        cap.read()

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        frame = cv2.flip(frame, 1)

        y_lo = cv2.getTrackbarPos("Y_min", 視窗名)
        y_hi = cv2.getTrackbarPos("Y_max", 視窗名)
        cr_lo = cv2.getTrackbarPos("Cr_min", 視窗名)
        cr_hi = cv2.getTrackbarPos("Cr_max", 視窗名)
        cb_lo = cv2.getTrackbarPos("Cb_min", 視窗名)
        cb_hi = cv2.getTrackbarPos("Cb_max", 視窗名)
        最小面積 = cv2.getTrackbarPos("MinArea_x100", 視窗名) * 100
        排除臉部開 = cv2.getTrackbarPos("ExcludeFace", 視窗名) == 1
        臉部擴張 = cv2.getTrackbarPos("FacePad_pct", 視窗名) / 100.0

        下限 = np.array([y_lo, cr_lo, cb_lo])
        上限 = np.array([y_hi, cr_hi, cb_hi])

        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        遮罩 = cv2.inRange(ycrcb, 下限, 上限)
        核心 = np.ones((5, 5), np.uint8)
        遮罩 = cv2.morphologyEx(遮罩, cv2.MORPH_OPEN, 核心)
        遮罩 = cv2.dilate(遮罩, 核心, iterations=2)

        顯示畫面 = frame.copy()
        臉部框列表 = []
        if 排除臉部開:
            灰階 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            臉部們 = 臉部偵測器.detectMultiScale(灰階, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60))
            for (fx, fy, fw, fh) in 臉部們:
                pad = int(fh * 臉部擴張)
                x0, y0 = max(0, fx - pad), max(0, fy - pad)
                x1 = min(frame.shape[1], fx + fw + pad)
                y1 = min(frame.shape[0], fy + fh + int(pad * 1.8))
                臉部框列表.append((x0, y0, x1, y1))
                cv2.rectangle(顯示畫面, (x0, y0), (x1, y1), (0, 0, 255), 2)
                cv2.putText(顯示畫面, "Face zone", (x0, max(0, y0 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # 挑「面積最大、重心不落在臉部框內」的候選色塊當手；重心落在框內的候選
        # 會被畫成粉紫色 rejected(face-like) 標出來，但不會動遮罩本身，
        # 所以就算跟臉部框有重疊，只要重心在框外的手還是能被正確選到
        contours, _ = cv2.findContours(遮罩, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        最大輪廓 = None
        最大面積 = 0
        for c in contours:
            a = cv2.contourArea(c)
            if a < 最小面積:
                continue
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            ccx, ccy = M["m10"] / M["m00"], M["m01"] / M["m00"]
            是臉 = any(x0 <= ccx <= x1 and y0 <= ccy <= y1 for (x0, y0, x1, y1) in 臉部框列表)
            if 是臉:
                cv2.drawContours(顯示畫面, [c], -1, (180, 0, 180), 1)
                cv2.putText(顯示畫面, "rejected(face-like)", (int(ccx) - 40, int(ccy)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 0, 180), 1)
                continue
            if a > 最大面積:
                最大輪廓, 最大面積 = c, a

        面積 = 最大面積
        手勢 = ""
        if 最大輪廓 is not None:
            凸包 = cv2.convexHull(最大輪廓)

            # 跟 hand_tracker.py 用同一套固實度/凸包缺陷算法跟門檻，
            # 讓這個調參工具看到的握拳/張手判斷結果跟遊戲裡一致
            固實度 = 1.0
            缺陷數 = 0
            try:
                凸包面積 = cv2.contourArea(凸包)
                固實度 = 面積 / 凸包面積 if 凸包面積 > 0 else 1.0
                凸包索引 = cv2.convexHull(最大輪廓, returnPoints=False)
                if 凸包索引 is not None and len(凸包索引) > 3:
                    缺陷 = cv2.convexityDefects(最大輪廓, 凸包索引)
                    if 缺陷 is not None:
                        for i in range(缺陷.shape[0]):
                            _, _, _, d = 缺陷[i, 0]
                            if d / 256.0 > 18:
                                缺陷數 += 1
            except Exception:
                pass

            手勢 = "握拳" if (固實度 > 0.85 and 缺陷數 < 2) else "張手"
            凸包色 = (0, 255, 255) if 手勢 == "握拳" else (0, 255, 0)  # 握拳=黃，張手=綠
            cv2.drawContours(顯示畫面, [凸包], -1, 凸包色, 2)

            M = cv2.moments(最大輪廓)
            if M["m00"] != 0:
                cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                cv2.circle(顯示畫面, (cx, cy), 6, (0, 0, 255), -1)
                cv2.circle(顯示畫面, (cx, cy), 10, (0, 255, 255), 2)

            手勢文字 = "Fist" if 手勢 == "握拳" else "Open"
            cv2.putText(顯示畫面, f"{手勢文字} solidity={固實度:.2f} defects={缺陷數}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 凸包色, 2)

        # 疊在畫面上的 overlay 文字用英文（cv2.putText 的 Hershey 字型不支援中文）；
        # 印到終端機的訊息維持中文，兩者用不同字串各自負責
        疊字 = f"Y[{y_lo},{y_hi}] Cr[{cr_lo},{cr_hi}] Cb[{cb_lo},{cb_hi}] MinArea={最小面積} Area={int(面積)}"
        if 手勢:
            疊字 += f" [{'Fist' if 手勢 == '握拳' else 'Open'}]"
        cv2.putText(顯示畫面, 疊字, (10, 顯示畫面.shape[0] - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        cv2.imshow(視窗名, 顯示畫面)
        cv2.imshow("Mask", 遮罩)

        數值文字 = f"Y[{y_lo},{y_hi}] Cr[{cr_lo},{cr_hi}] Cb[{cb_lo},{cb_hi}] 最小面積={最小面積} 目前面積={int(面積)}"
        if 數值文字 != 上次列印:
            print(數值文字)
            上次列印 = 數值文字

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n---- 把下面兩行貼回 hand_tracker.py 的 __init__（取代原本的膚色下限/上限）----")
    print(f"self.膚色下限 = np.array([{y_lo}, {cr_lo}, {cb_lo}])")
    print(f"self.膚色上限 = np.array([{y_hi}, {cr_hi}, {cb_hi}])")


if __name__ == "__main__":
    main()
