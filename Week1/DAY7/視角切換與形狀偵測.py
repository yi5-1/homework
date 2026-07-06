# 即時 webcam 影像處理：可切換 原始/灰階/模糊/Canny/形狀偵測 五種畫面
# 所有參數用 slider (trackbar) 即時調整
# 形狀偵測模式下：可勾選要顯示哪些形狀（三角形、正方形/矩形、圓形、多邊形）

import cv2
import numpy as np

def nothing(x):
    """trackbar 的 callback，什麼都不做（我們每次 loop 自己讀值）"""
    pass


# ====== 開啟 webcam ======
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("錯誤：無法開啟視訊鏡頭")
    exit()

print("按 q 離開；按 s 存下目前畫面到 snapshot.png")


# ====== 建立控制面板 ======
cv2.namedWindow('Controls', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Controls', 420, 520)

# 視角切換：0=原始, 1=灰階, 2=模糊, 3=Canny, 4=形狀偵測
cv2.createTrackbar('View 0RAW 1GRAY 2BLUR 3CANNY 4SHAPE', 'Controls', 4, 4, nothing)

# 模糊參數
cv2.createTrackbar('Blur ksize',       'Controls', 7,  30, nothing)   # 會強制轉奇數
cv2.createTrackbar('Blur sigma x10',   'Controls', 15, 100, nothing)  # 除以 10 → 0~10.0

# Canny 邊緣參數
cv2.createTrackbar('Canny T1',         'Controls', 30, 500, nothing)
cv2.createTrackbar('Canny T2',         'Controls', 150, 500, nothing)

# 形狀偵測面積範圍
cv2.createTrackbar('Min Area',         'Controls', 500,  20000, nothing)
cv2.createTrackbar('Max Area x10',     'Controls', 5000, 20000, nothing)  # ×10 → 上限 200000

# 多邊形逼近精準度 (approxPolyDP 的 epsilon 比例)
cv2.createTrackbar('Epsilon %',        'Controls', 4, 15, nothing)   # 除以 100 → 0.04

# 圓度門檻 (0.01 * value)：4πA / P² 越接近 1 越像圓
cv2.createTrackbar('Circle Thresh %',  'Controls', 75, 100, nothing)  # → 0.75

# 各形狀開關
cv2.createTrackbar('Show Triangle',    'Controls', 1, 1, nothing)
cv2.createTrackbar('Show Square/Rect', 'Controls', 1, 1, nothing)
cv2.createTrackbar('Show Circle',      'Controls', 1, 1, nothing)
cv2.createTrackbar('Show Polygon 5+',  'Controls', 0, 1, nothing)


VIEW_NAMES = ["Raw (BGR)", "Gray", "Blur", "Canny", "Shape Detection"]

while True:
    ret, frame = cap.read()
    if not ret:
        print("錯誤：無法讀取畫面")
        break

    # ====== 讀 trackbar ======
    view       = cv2.getTrackbarPos('View 0RAW 1GRAY 2BLUR 3CANNY 4SHAPE', 'Controls')
    ksize      = max(1, cv2.getTrackbarPos('Blur ksize', 'Controls'))
    if ksize % 2 == 0:
        ksize += 1                             # Gaussian ksize 必須是奇數
    sigma      = cv2.getTrackbarPos('Blur sigma x10', 'Controls') / 10.0
    t1         = cv2.getTrackbarPos('Canny T1', 'Controls')
    t2         = cv2.getTrackbarPos('Canny T2', 'Controls')
    min_area   = cv2.getTrackbarPos('Min Area', 'Controls')
    max_area   = cv2.getTrackbarPos('Max Area x10', 'Controls') * 10
    eps_pct    = max(cv2.getTrackbarPos('Epsilon %', 'Controls'), 1) / 100.0
    circ_thr   = cv2.getTrackbarPos('Circle Thresh %', 'Controls') / 100.0
    show_tri   = cv2.getTrackbarPos('Show Triangle',    'Controls')
    show_sq    = cv2.getTrackbarPos('Show Square/Rect', 'Controls')
    show_ci    = cv2.getTrackbarPos('Show Circle',      'Controls')
    show_pg    = cv2.getTrackbarPos('Show Polygon 5+',  'Controls')

    # ====== 影像處理 pipeline ======
    # 每一階段都算，方便切換不用重跑
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur  = cv2.GaussianBlur(gray, (ksize, ksize), sigma)
    edges = cv2.Canny(blur, t1, t2)

    # ====== 依 view 選擇要顯示的畫面 ======
    if view == 0:
        display = frame.copy()
    elif view == 1:
        display = cv2.cvtColor(gray,  cv2.COLOR_GRAY2BGR)
    elif view == 2:
        display = cv2.cvtColor(blur,  cv2.COLOR_GRAY2BGR)
    elif view == 3:
        display = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    else:
        # ====== Shape Detection 模式 ======
        display = frame.copy()
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        counts = {"Triangle": 0, "Square": 0, "Rectangle": 0, "Circle": 0, "Polygon": 0}

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue

            perimeter = cv2.arcLength(cnt, True)
            if perimeter <= 0:
                continue

            # 凸包 + 多邊形逼近
            hull   = cv2.convexHull(cnt)
            eps    = eps_pct * cv2.arcLength(hull, True)
            approx = cv2.approxPolyDP(hull, eps, True)
            vtx    = len(approx)

            # 圓度：4πA / P²，圓形時接近 1
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            # 中心點
            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            shape = None
            color = (255, 255, 255)

            # 判斷順序：圓 → 三角形 → 四邊形 → 多邊形
            if show_ci and circularity > circ_thr and vtx >= 5:
                shape = "Circle"
                color = (0, 0, 255)                  # 紅
                counts["Circle"] += 1
            elif show_tri and vtx == 3:
                shape = "Triangle"
                color = (0, 255, 255)                # 黃
                counts["Triangle"] += 1
            elif show_sq and vtx == 4:
                x, y, w, h = cv2.boundingRect(approx)
                ratio = w / float(h) if h > 0 else 0
                if 0.85 <= ratio <= 1.15:
                    shape = "Square"
                    counts["Square"] += 1
                else:
                    shape = "Rectangle"
                    counts["Rectangle"] += 1
                color = (0, 255, 0)                  # 綠
            elif show_pg and vtx >= 5:
                shape = f"Polygon-{vtx}"
                color = (255, 100, 200)              # 粉
                counts["Polygon"] += 1

            if shape:
                cv2.drawContours(display, [approx], -1, color, 2)
                cv2.circle(display, (cX, cY), 4, color, -1)
                cv2.putText(display, f"{shape}  A:{int(area)}",
                            (cX - 55, cY - 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        # 右上角統計數量
        stat_y = 30
        for name, n in counts.items():
            if n > 0:
                cv2.putText(display, f"{name}: {n}",
                            (display.shape[1] - 180, stat_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                stat_y += 22

    # ====== 頂部 label + 操作提示 ======
    cv2.putText(display, VIEW_NAMES[view], (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(display, "q=Quit  s=Save snapshot.png",
                (10, display.shape[0] - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    cv2.imshow('Preview', display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite('snapshot.png', display)
        print("已存 snapshot.png")

cap.release()
cv2.destroyAllWindows()
