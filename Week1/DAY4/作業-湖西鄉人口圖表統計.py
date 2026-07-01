import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_excel(r'C:\Users\TSIC\Documents\project\Week1\DAY4\data.xlsx', header=None, skiprows=1)

years  = df.iloc[:, 0].astype(int).tolist()
months = df.iloc[:, 1].astype(int).tolist()
births = df.iloc[:, 8].astype(int).tolist()
deaths = df.iloc[:, 9].astype(int).tolist()

labels = [f'{y}/{m:02d}' for y, m in zip(years, months)]
diff = [b - d for b, d in zip(births, deaths)]
colors = ['#2E86DE' if v >= 0 else '#E74C3C' for v in diff]

x = range(len(labels))

plt.figure(figsize=(14, 5))
plt.bar(x, diff, color=colors)
plt.axhline(0, color='black', linewidth=0.8)

plt.xticks(x, labels, rotation=75, fontsize=8)
plt.xlabel('年/月')
plt.ylabel('出生 - 死亡 (人)')
plt.title('湖西鄉 每月自然增加人口 (出生 - 死亡)')

from matplotlib.patches import Patch
plt.legend(handles=[
    Patch(color='#2E86DE', label='正成長 (出生 > 死亡)'),
    Patch(color='#E74C3C', label='負成長 (出生 < 死亡)'),
])
plt.tight_layout()
plt.show()
