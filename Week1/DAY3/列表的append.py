import math 
import matplotlib.pyplot as plt
x= []
y= []
for i in range(100):
    x.append(i+1)
    y.append(math.pow(i+1,2)+(i+1)+1)
    print(y)
# 2. 繪製折線圖
plt.plot(x, y)
# 3. 顯示圖表
plt.show()