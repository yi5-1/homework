import matplotlib.pyplot as plt
# 1. 準備數據（例如：10 個學生的微積分成績）

data = [55,62, 67, 75, 78, 81, 85, 88, 92, 98]
# 2. 繪製直方圖（bins 代表要分成幾組，這裡分成 5 組）
plt.hist(data,bins=5 ,edgecolor='black')
# 3. 顯示圖表
plt.show()