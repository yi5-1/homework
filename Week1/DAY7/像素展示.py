import cv2
# 1. 讀取圖片
# 請將 'your_image.jpg' 替換成你實際的圖片路徑
# 第二個參數 cv2.IMREAD_COLOR 代表讀取彩色圖片（預設值）
img = cv2.imread(r'C:\Users\TSIC\Documents\project\Week1\DAY7\WIN_20260703_09_51_29_Pro.jpg')
# 2. 檢查圖片是否成功讀取（路徑寫錯或檔案損壞會讀到 None）
if img is None:
    print("錯誤：無法讀取圖片，請檢查檔案路徑是否正確！")
    exit()
# 3. 顯示圖片
# 第一個參數是視窗名稱，第二個參數是要顯示的影像矩陣
cv2.imshow('Image Viewer', img)
# 4. 等待使用者按下鍵盤任意鍵
# 參數 0 代表無限期等待，直到按下鍵盤為止
cv2.waitKey(0)

# 5. 關閉所有 OpenCV 建立的視窗
cv2.destroyAllWindows()