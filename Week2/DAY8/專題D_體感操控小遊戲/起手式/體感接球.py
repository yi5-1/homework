# 專題 D 起手式：體感操控小遊戲（能跑的最小骨架）
#
# 玩法：用鏡頭偵測「綠色物體」的左右位置來移動底部的接盤，接住掉下來的球得分。
# 沒有鏡頭 / 偵測不到時，會自動 fallback 成滑鼠控制，程式一樣能玩。
#
# 核心觀念：OpenCV 和 pygame 在同一個迴圈裡輪流跑
#   每一格 → 讀鏡頭 → HSV inRange 找綠色 → 最大色塊中心 x → 換算成接盤 x
#
# 你要接手加的：
#   - 校準顏色（不同環境光）、加握拳/張開兩種動作、疊鏡頭小畫面、做成兩人連線對戰

import cv2
import numpy as np
import pygame

# ---- 綠色的 HSV 範圍（偵測不準就調這裡，或改成你的色卡顏色）----
綠色下限 = np.array([35, 80, 80])
綠色上限 = np.array([85, 255, 255])
最小色塊面積 = 800  # 太小的雜訊不算

寬, 高 = 800, 600


def 找綠色中心x(frame):
    """回傳綠色色塊中心的 x（0~1 比例），找不到回傳 None。"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    遮罩 = cv2.inRange(hsv, 綠色下限, 綠色上限)
    contours, _ = cv2.findContours(遮罩, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    最大 = max(contours, key=cv2.contourArea)
    if cv2.contourArea(最大) < 最小色塊面積:
        return None
    M = cv2.moments(最大)
    if M["m00"] == 0:
        return None
    cx = M["m10"] / M["m00"]
    # 鏡頭是鏡像，畫面左右要翻過來才符合直覺
    return 1.0 - cx / frame.shape[1]


def main():
    pygame.init()
    螢幕 = pygame.display.set_mode((寬, 高))
    pygame.display.set_caption("體感接球")
    clock = pygame.time.Clock()
    字型 = pygame.font.SysFont("Microsoft JhengHei", 28)

    cap = cv2.VideoCapture(0)
    有鏡頭 = cap.isOpened()
    if not 有鏡頭:
        print("沒有鏡頭，改用滑鼠控制。")

    接盤 = pygame.Rect(寬 // 2 - 60, 高 - 40, 120, 20)
    球 = pygame.Rect(np.random.randint(0, 寬 - 30), 0, 30, 30)
    球速 = 6
    分數 = 0
    命 = 3

    while 命 > 0:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                命 = 0

        # --- 控制：優先用鏡頭，失敗就用滑鼠 ---
        目標x = None
        if 有鏡頭:
            ret, frame = cap.read()
            if ret:
                比例 = 找綠色中心x(frame)
                if 比例 is not None:
                    目標x = 比例 * 寬
        if 目標x is None:
            目標x = pygame.mouse.get_pos()[0]
        接盤.centerx = int(目標x)
        接盤.clamp_ip(螢幕.get_rect())

        # --- 球掉落 ---
        球.y += 球速
        if 球.colliderect(接盤):
            分數 += 1
            球.x, 球.y = np.random.randint(0, 寬 - 30), 0
            球速 = min(球速 + 0.3, 14)  # TODO(加分)：難度曲線自己調
        elif 球.y > 高:
            命 -= 1
            球.x, 球.y = np.random.randint(0, 寬 - 30), 0

        # --- 畫面 ---
        螢幕.fill((20, 20, 30))
        pygame.draw.rect(螢幕, (76, 114, 176), 接盤, border_radius=6)
        pygame.draw.ellipse(螢幕, (221, 132, 82), 球)
        螢幕.blit(字型.render(f"分數 {分數}   命 {命}", True, (255, 255, 255)), (10, 10))
        控制方式 = "鏡頭" if (有鏡頭 and 目標x) else "滑鼠"
        螢幕.blit(字型.render(f"控制：{控制方式}（拿綠色物體移動）", True, (180, 180, 180)), (10, 45))
        pygame.display.flip()
        clock.tick(60)

    if 有鏡頭:
        cap.release()
    pygame.quit()
    print("遊戲結束，最終分數：", 分數)


if __name__ == "__main__":
    main()
