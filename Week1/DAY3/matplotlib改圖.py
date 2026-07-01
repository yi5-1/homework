import math 
import matplotlib.pyplot as plt
plt.rc('font', family='Microsoft JhengHei')
plt.rcParams['axes.unicode_minus'] = False
x= []
y= []
for i in range(-50,51):
    x.append(i+1)
    y.append(math.pow(i+1,2)+(i+1)+1)
    print(y)
# 2. 繪製折線圖
plt.plot(x, y)
plt.xlim(-60, 60)
plt.ylim(-200, 3000)
plt.title("我是標題")
plt.xlabel("X 軸數據")
plt.ylabel("Y 軸數據")
# 3. 顯示圖表
plt.show()