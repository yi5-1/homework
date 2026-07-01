import math
def 射射射(v0,angle):
    g = 9.8  
    theta = math.radians(angle)
    # 3. 帶入公式計算
    T = (2 * v0 * math.sin(theta)) / g            # 飛行總時間
    H = ((v0 * math.sin(theta)) ** 2) / (2 * g)   # 最大高度
    R = (v0 ** 2 * math.sin(2 * theta)) / g       # 水平射程
    return T,H,R
T , H , R = 射射射(25,45)
# 4. 印出結果（保留小數點後兩位）
print(f"--- 斜向拋射計算結果 (初速: {25} m/s, 角度: {45}°) ---")
print(f"飛行總時間 (T): {T:.2f} 秒")
print(f"最大高度 (H)  : {H:.2f} 公尺")
print(f"水平射程 (R)  : {R:.2f} 公尺")