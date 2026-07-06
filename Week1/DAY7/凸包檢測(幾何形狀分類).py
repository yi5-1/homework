import cv2
import numpy as np

# 1. 建立 VideoCapture 物件
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("錯誤：無法開啟視訊鏡頭。")
    exit()

print("鏡頭已開啟！幾何形狀檢測中... 按下 'q' 鍵可結束程式。")

# 定義目標面積區間
min_area = 500   # 稍微調大一點點，避免雜訊
max_area = 50000 

while True:
    ret, frame = cap.read()
    if not ret:
        print("錯誤：無法接收影像畫面。")
        break

    img_copy = frame.copy()
    
    # 影像預處理
    gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_img, (7, 7), 1.5)
    
    # A. 邊緣與輪廓檢測
    edges = cv2.Canny(blurred, 50, 150)
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # B. 霍夫圓檢測 (預備給圓形比對使用)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                               param1=100, param2=35, minRadius=10, maxRadius=200)
    if circles is not None:
        circles = np.uint16(np.around(circles))

    for cnt in contours:
        # 1. 面積條件過濾
        area = cv2.contourArea(cnt)
        if min_area <= area <= max_area:
            
            # 2. 凸包檢測 (Convex Hull)
            hull = cv2.convexHull(cnt)
            
            # 3. 多邊形逼近 (Polygon Approximation)
            # 這裡的 0.04 是逼近精準度，可根據視訊鏡頭品質微調 (通常在 0.02 ~ 0.05 之間)
            epsilon = 0.04 * cv2.arcLength(hull, True)
            approx = cv2.approxPolyDP(hull, epsilon, True)
            
            # 計算形狀的中心點
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                continue

            shape_label = "Unknown"
            color = (255, 255, 255) # 預設白色
            vertices_count = len(approx)

            # 4. 依據幾何特徵進行分類
            
            # 【情況 A：三角形】
            if vertices_count == 3:
                shape_label = "Triangle"
                color = (0, 255, 255)  # 黃色
                
            # 【情況 B：正方形/四邊形】
            elif vertices_count == 4:
                shape_label = "Square"
                color = (0, 255, 0)    # 綠色
                
            # 【情況 C：圓形辨識】(頂點數較多時，結合霍夫圓比對)
            elif vertices_count > 4 and circles is not None:
                for circle in circles[0, :]:
                    h_x, h_y, _ = circle[0], circle[1], circle[2]
                    distance = np.sqrt((cX - h_x)**2 + (cY - h_y)**2)
                    
                    if distance < 20: # 圓心距離在合理範圍內
                        shape_label = "Circle"
                        color = (0, 0, 255)  # 紅色
                        break
            
            # 5. 如果成功分類，就繪製出來
            if shape_label != "Unknown":
                # 繪製凸包輪廓
                cv2.drawContours(img_copy, [hull], -1, color, 2)
                
                # 繪製中心點
                cv2.circle(img_copy, (cX, cY), 4, color, -1)
                
                # 標註圖形名稱與面積
                text = f"{shape_label} (A:{int(area)})"
                cv2.putText(img_copy, text, (cX - 40, cY - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # 3. 顯示結果
    cv2.imshow('Webcam Shape Detection', img_copy)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()