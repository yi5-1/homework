import cv2
import numpy as np

# 1. 建立 VideoCapture 物件
cap = cv2.VideoCapture(0)

# 檢查鏡頭是否成功開啟
if not cap.isOpened():
    print("錯誤：無法開啟視訊鏡頭。")
    exit()

print("鏡頭已開啟！按下 'q' 鍵可結束程式。")

# 定義面積區間
min_area = 500   # 最小面積限制
max_area = 50000 # 最大面積限制 

while True:
    # 2. 逐影格（Frame）讀取影像
    ret, frame = cap.read()
    
    # 如果讀取失敗，直接跳出迴圈
    if not ret:
        print("錯誤：無法接收影像畫面。")
        break

    img_copy = frame.copy()
    
    # 影像預處理：轉灰階 + 高斯模糊（霍夫圓對雜訊很敏感，模糊非常關鍵）
    gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_img, (13, 13), 2)
    
    # A. 進行 Canny 與輪廓檢測 (用來篩選面積)
    edges = cv2.Canny(blurred, 50, 150)
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # B. 進行霍夫圓檢測
    # dp=1 (解析度), minDist=50 (圓心間的最小距離), param1=Canny高閾值, param2=圓心檢測閾值(越小越容易誤判)
    # minRadius/maxRadius 可根據實際大小調整，設為 0 代表不限制
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                               param1=100, param2=35, minRadius=10, maxRadius=200)
    
    count = 0
    
    # 如果有偵測到任何霍夫圓，才開始與輪廓進行比對
    if circles is not None and len(contours) > 0:
        # 將圓的座標轉為整數
        circles = np.uint16(np.around(circles))
        
        for cnt in contours:
            # 1. 檢查面積條件
            area = cv2.contourArea(cnt)
            if min_area <= area <= max_area:
                
                # 2. 計算輪廓中心點 (Moments)
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    
                    # 3. 驗證這個輪廓附近有沒有對應的霍夫圓 (比對圓心距離)
                    is_circle = False
                    matched_radius = 0
                    
                    for circle in circles[0, :]:
                        h_x, h_y, h_r = circle[0], circle[1], circle[2]
                        # 計算輪廓中心與霍夫圓心的歐幾里得距離
                        distance = np.sqrt((cX - h_x)**2 + (cY - h_y)**2)
                        
                        # 如果距離小於 15 像素，我們就認定這個輪廓「確實是個圓」
                        if distance < 15:
                            is_circle = True
                            matched_radius = h_r
                            break
                    
                    # 4. 條件完全滿足：在面積區間內，且是個圓 ➔ 繪製出來
                    if is_circle:
                        count += 1
                        
                        # 繪製輪廓 (紅色)
                        cv2.drawContours(img_copy, [cnt], -1, (0, 0, 255), 2)
                        
                        # 繪製圓心 (綠色點)
                        cv2.circle(img_copy, (cX, cY), 3, (0, 255, 0), -1)
                        
                        # 標註資訊
                        cv2.putText(img_copy, f"Circle #{count} R:{matched_radius}", (cX - 30, cY - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    # 3. 顯示影像畫面
    cv2.imshow('Webcam', img_copy)
    # 可選：想觀察邊緣可以打開下一行
    # cv2.imshow('Edges', edges)

    # 4. 按下 'q' 鍵結束
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 5. 釋放資源
cap.release()
cv2.destroyAllWindows()