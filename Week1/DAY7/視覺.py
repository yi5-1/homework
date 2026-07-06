import cv2

# 1. 建立 VideoCapture 物件。參數 0 通常代表內建的預設鏡頭。
# 如果有接外接鏡頭，可以嘗試改為 1, 2 等。
cap = cv2.VideoCapture(0)

# 檢查鏡頭是否成功開啟
if not cap.isOpened():
    print("錯誤：無法開啟視訊鏡頭。")
    exit()

print("鏡頭已開啟！按下 'q' 鍵可結束程式。")

while True:
    # 2. 逐影格（Frame）讀取影像
    # ret 是布林值，代表成功讀取與否；frame 是該影格的影像矩陣
    ret, frame = cap.read()
    灰色的圖片 = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)#彩圖轉灰階
    邊緣檢測 = cv2.Canny(灰色的圖片, 100, 200)
    img_copy = frame.copy()
    #opencv找輪廓的指令
    contours, hierarchy = cv2.findContours(邊緣檢測, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = 500   # 最小面積限制
    max_area = 50000 # 最大面積限制 

    count = 0
    for i, cnt in enumerate(contours):
        # 計算該輪廓的面積
        area = cv2.contourArea(cnt)
        # 判斷面積是否在設定的區間內
        if min_area <= area <= max_area:
            count += 1
            print(f"符合輪廓 {count}: 面積 = {area:.2f}")
            
            # 5. 繪製符合條件的輪廓
            # 參數: (要畫在哪張圖, 輪廓列表, -1代表畫出該index的單個輪廓, 顏色(B,G,R), 線條粗細)
            cv2.drawContours(img_copy, [cnt], -1, (0, 0, 255), 2)  # 用紅色(0,0,255)畫出輪廓
            
            # 【可選進階】計算輪廓的中心點並加上文字標籤
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                # 在中心點標註這是第幾個符合的物體與其面積
                cv2.putText(img_copy, f"#{count} (A:{int(area)})", (cX - 20, cY), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    
    # 如果讀取失敗，就跳出迴圈
    if not ret:
        print("錯誤：無法接收影像畫面。")
        break

    # 3. 顯示影像畫面，視窗名稱為 'Webcam'
    cv2.imshow('Webcam', img_copy)

    # 4. 等待 1 毫秒，並偵測是否按下了 'q' 鍵
    # 0xFF 是為了只取最後一個位元組，確保在不同平台上鍵盤碼正確
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 5. 釋放鏡頭資源並關閉所有 OpenCV 視窗
cap.release()
cv2.destroyAllWindows()