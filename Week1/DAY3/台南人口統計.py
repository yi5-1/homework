import csv
from pathlib import Path
import matplotlib.pyplot as plt
plt.rc('font', family='Microsoft JhengHei')
plt.rcParams['axes.unicode_minus'] = False
# Step 1: Read CSV
csv_path = Path(__file__).parent / '985ed9fd-c6a3-4421-9886-79621e170322.csv'
districts = []
populations = []
with open(csv_path, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = [col.strip('\ufeff') for col in next(reader)]
    for row in reader:
        data = dict(zip(header, row))
        if data['區域別'] == '臺南市':
            continue
        districts.append(data['區域別'])
        populations.append(int(data['人口數總計']))

# Step 2: Plot pie chart
plt.figure(figsize=(10, 10))
plt.pie(populations, labels=districts, autopct='%1.1f%%')
plt.title('臺南市各區人口比例')
plt.axis('equal')
plt.show()
