# 專題 D — 體感操控小遊戲：閃避隕石
#
# 玩法：
#   張手（open hand）→ 飛船左右移動（飛行）
#   握拳（fist）    → 停止 + 射擊（消耗彈藥）
#   射擊時無法移動，需放開手才能繼續飛行
#   彈藥從天而降（綠色方塊），撿到才能射，最多 3 發
#   分數由存活時間累計（0.1 秒 = 10 分）
#
#   開始前輸入姓名，結束後顯示今日排行前 5 名
#
#   手勢判斷原理（參考 Week1/DAY7/凸包檢測(幾何形狀分類).py）：
#     1. HSV inRange → 高斯模糊去雜訊 → 找最大輪廓
#     2. 計算凸包缺陷（convexityDefects）：張開手指會產生多個深缺陷
#     3. 缺陷數 >= 2 → 張手；缺陷數 < 2 → 握拳
#     4. 若缺陷計算失敗，fallback 到固實度（solidity）

import cv2
import numpy as np
import pygame
import random
import datetime
import json
import os

# ===== HSV 顏色設定（綠色物體 / 手套）=====
綠色下限 = np.array([35, 80, 80])
綠色上限 = np.array([85, 255, 255])
最小色塊面積 = 800

寬, 高 = 800, 600

# ===== 手勢判斷參數 =====
缺陷深度閾值 = 15
手勢閾值 = 0.78

# ===== 排行檔案 =====
排行檔案 = os.path.join(os.path.dirname(__file__), "ranking.json")


def 讀取排行():
    """回傳 [{name, score, date}, ...] 依 score 降冪"""
    if not os.path.exists(排行檔案):
        return []
    with open(排行檔案, "r", encoding="utf-8") as f:
        return json.load(f)


def 儲存排行(資料):
    with open(排行檔案, "w", encoding="utf-8") as f:
        json.dump(資料, f, ensure_ascii=False, indent=2)


def 取得今日排行():
    """回傳今日前 5 名"""
    全部 = 讀取排行()
    今日 = datetime.date.today().isoformat()
    今日資料 = [e for e in 全部 if e.get("date") == 今日]
    今日資料.sort(key=lambda e: e["score"], reverse=True)
    return 今日資料[:5]


def 新增排行(name, score):
    全部 = 讀取排行()
    全部.append({
        "name": name,
        "score": score,
        "date": datetime.date.today().isoformat(),
    })
    儲存排行(全部)


def 輸入姓名(螢幕, 字型, 大字型, cap, 最近frame):
    """在 pygame 中讓使用者輸入姓名，回傳姓名字串"""
    姓名 = ""
    輸入中 = True
    clock = pygame.time.Clock()

    while 輸入中:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and len(姓名) > 0:
                    輸入中 = False
                elif e.key == pygame.K_BACKSPACE:
                    姓名 = 姓名[:-1]
                elif e.key == pygame.K_ESCAPE:
                    return None
                elif len(e.unicode) > 0 and len(姓名) < 12:
                    姓名 += e.unicode

        螢幕.fill((12, 12, 28))

        # 背景星星
        for _ in range(60):
            sx = (_ * 137) % 寬
            sy = (_ * 211) % 高
            pygame.draw.circle(螢幕, (60, 60, 80), (sx, sy), 1)

        # 標題
        t = 大字型.render("體感閃避隕石", True, (0, 180, 255))
        螢幕.blit(t, (寬 // 2 - t.get_width() // 2, 高 // 2 - 120))
        t2 = 字型.render("請輸入姓名後按 Enter", True, (200, 200, 200))
        螢幕.blit(t2, (寬 // 2 - t2.get_width() // 2, 高 // 2 - 70))

        # 輸入框
        box_w, box_h = 300, 50
        box_x, box_y = 寬 // 2 - box_w // 2, 高 // 2 - box_h // 2
        pygame.draw.rect(螢幕, (50, 50, 70), (box_x, box_y, box_w, box_h), border_radius=6)
        pygame.draw.rect(螢幕, (0, 180, 255), (box_x, box_y, box_w, box_h), 2, border_radius=6)

        顯示文字 = 姓名 + ("|" if pygame.time.get_ticks() % 1000 < 500 else "")
        輸入表面 = 字型.render(顯示文字, True, (255, 255, 255))
        螢幕.blit(輸入表面, (box_x + 10, box_y + (box_h - 輸入表面.get_height()) // 2))

        # 鏡頭小畫面（左上角）
        if cap is not None and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                最近frame = frame.copy()
                小 = cv2.resize(frame, (160, 120))
                小 = cv2.flip(小, 1)
                小 = cv2.cvtColor(小, cv2.COLOR_BGR2RGB)
                小 = np.transpose(小, (1, 0, 2))
                預覽 = pygame.surfarray.make_surface(小)
                螢幕.blit(預覽, (10, 10))
                pygame.draw.rect(螢幕, (100, 100, 100), (9, 9, 162, 122), 1)

        pygame.display.flip()
        clock.tick(30)

    return 姓名


def 找綠色中心x(frame):
    """回傳 (比例x, 固實度, 缺陷數)。"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    遮罩 = cv2.inRange(hsv, 綠色下限, 綠色上限)
    遮罩 = cv2.GaussianBlur(遮罩, (5, 5), 0)

    contours, _ = cv2.findContours(遮罩, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None, 0
    最大 = max(contours, key=cv2.contourArea)
    if cv2.contourArea(最大) < 最小色塊面積:
        return None, None, 0
    M = cv2.moments(最大)
    if M["m00"] == 0:
        return None, None, 0
    cx = M["m10"] / M["m00"]

    比例x = 1.0 - cx / frame.shape[1]

    凸包 = cv2.convexHull(最大)
    凸包面積 = cv2.contourArea(凸包)
    固實度 = cv2.contourArea(最大) / 凸包面積 if 凸包面積 > 0 else 1.0

    缺陷數 = 0
    凸包索引 = cv2.convexHull(最大, returnPoints=False)
    if 凸包索引 is not None and 凸包索引.shape[0] > 3:
        缺陷 = cv2.convexityDefects(最大, 凸包索引)
        if 缺陷 is not None:
            for i in range(缺陷.shape[0]):
                d = 缺陷[i, 0][3] / 256.0
                if d > 缺陷深度閾值:
                    缺陷數 += 1

    return 比例x, 固實度, 缺陷數


def 繪製飛船(螢幕, rect, 飛行中):
    pygame.draw.polygon(螢幕, (0, 180, 255), [
        (rect.centerx, rect.top),
        (rect.left, rect.bottom - 5),
        (rect.right, rect.bottom - 5),
    ])
    if 飛行中:
        火焰長 = 10 + int(8 * np.sin(pygame.time.get_ticks() * 0.01))
        pygame.draw.polygon(螢幕, (255, 180, 50), [
            (rect.centerx - 8, rect.bottom - 5),
            (rect.centerx + 8, rect.bottom - 5),
            (rect.centerx, rect.bottom - 5 + 火焰長),
        ])


def main():
    pygame.init()
    螢幕 = pygame.display.set_mode((寬, 高))
    pygame.display.set_caption("體感閃避隕石")
    clock = pygame.time.Clock()
    字型 = pygame.font.SysFont("Microsoft JhengHei", 26)
    大字型 = pygame.font.SysFont("Microsoft JhengHei", 48)
    小字型 = pygame.font.SysFont("Microsoft JhengHei", 22)

    # ---- 鏡頭 ----
    cap = cv2.VideoCapture(0)
    有鏡頭 = cap.isOpened()
    最近frame = None
    if not 有鏡頭:
        print("[!] 無鏡頭，無法啟動純手控模式")
        pygame.quit()
        return

    # ---- 輸入姓名 ----
    玩家名 = 輸入姓名(螢幕, 字型, 大字型, cap, 最近frame)
    if 玩家名 is None:
        cap.release()
        pygame.quit()
        return

    # ---- 玩家 ----
    飛船 = pygame.Rect(寬 // 2 - 25, 高 - 70, 50, 30)
    飛行中 = True
    最後比例x = 0.5

    # ---- 隕石 ----
    隕石列表 = []
    隕石倒數 = 0
    隕石間隔 = 35
    基礎速度 = 3

    # ---- 子彈 ----
    子彈列表 = []
    子彈速度 = 10
    彈藥數 = 0
    最大彈藥 = 3

    # ---- 彈藥補給 ----
    補給列表 = []
    補給倒數 = 0
    補給間隔 = 150

    # ---- 遊戲狀態 ----
    總分 = 0
    命 = 3
    遊戲中 = True
    遊戲結束旗 = False
    手已偵測 = False
    開始時間 = 0  # pygame ticks when game actually starts

    # ---- 手勢 ----
    連射延遲 = 0

    while 遊戲中:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                遊戲中 = False

        # ===== 鏡頭偵測 =====
        目標x = None
        手勢 = "張手"
        固實度值 = None
        比例x = None
        缺陷數 = 0

        if 有鏡頭:
            ret, frame = cap.read()
            if ret:
                最近frame = frame.copy()
                比例x, 固實度值, 缺陷數 = 找綠色中心x(frame)
                if 比例x is not None:
                    目標x = 比例x * 寬
                    最後比例x = 比例x
                    if not 手已偵測:
                        手已偵測 = True
                        開始時間 = pygame.time.get_ticks()
                    if 缺陷數 >= 2:
                        手勢 = "張手"
                    elif 缺陷數 == 1:
                        手勢 = "握拳"
                    else:
                        手勢 = "握拳" if 固實度值 > 手勢閾值 else "張手"

        # ===== 遊戲邏輯 =====
        if 手已偵測:
            存活ms = pygame.time.get_ticks() - 開始時間
            存活秒 = 存活ms / 1000
            總分 = int(存活ms // 10)  # 0.1 秒 = 10 分 → 1 ms = 0.1 分 → 每 10 ms = 1 分

            飛行中 = (手勢 == "張手")

            if 飛行中:
                飛船.centerx = int(目標x)
                飛船.clamp_ip(螢幕.get_rect())
            else:
                if 連射延遲 <= 0 and 彈藥數 > 0:
                    子彈列表.append(pygame.Rect(飛船.centerx - 3, 飛船.top - 5, 6, 18))
                    彈藥數 -= 1
                    連射延遲 = 12
            連射延遲 -= 1

            # ---- 產生隕石 ----
            隕石倒數 += 1
            if 隕石倒數 >= 隕石間隔:
                隕石倒數 = 0
                x = random.randint(0, 寬 - 40)
                大小 = random.randint(22, 52)
                vy = 基礎速度 + random.randint(0, 3)
                vx = random.randint(-2, 2)
                隕石列表.append({
                    "rect": pygame.Rect(x, -大小, 大小, 大小),
                    "vx": vx,
                    "vy": vy,
                    "rot": random.uniform(0, 360),
                    "rot_speed": random.uniform(-3, 3),
                })

            # ---- 產生彈藥補給 ----
            補給倒數 += 1
            if 補給倒數 >= 補給間隔 and 彈藥數 < 最大彈藥:
                補給倒數 = 0
                x = random.randint(0, 寬 - 22)
                補給列表.append({
                    "rect": pygame.Rect(x, -22, 22, 22),
                    "vy": 2.5,
                })

            # ---- 更新隕石 ----
            for m in 隕石列表[:]:
                m["rect"].x += m["vx"]
                m["rect"].y += m["vy"]
                m["rot"] += m["rot_speed"]
                if (m["rect"].top > 高 + 20 or m["rect"].left < -60 or
                        m["rect"].right > 寬 + 60):
                    隕石列表.remove(m)
                    continue
                if m["rect"].colliderect(飛船):
                    命 -= 1
                    隕石列表.remove(m)
                    if 命 <= 0:
                        遊戲結束旗 = True
                    continue

            # ---- 更新子彈 ----
            for b in 子彈列表[:]:
                b.y -= 子彈速度
                if b.bottom < 0:
                    子彈列表.remove(b)
                    continue
                for m in 隕石列表[:]:
                    if b.colliderect(m["rect"]):
                        子彈列表.remove(b)
                        隕石列表.remove(m)
                        break

            # ---- 更新彈藥補給 ----
            for p in 補給列表[:]:
                p["rect"].y += p["vy"]
                if p["rect"].top > 高:
                    補給列表.remove(p)
                    continue
                if p["rect"].colliderect(飛船) and 彈藥數 < 最大彈藥:
                    彈藥數 += 1
                    補給列表.remove(p)

            # ---- 難度遞增（依存活時間）----
            隕石間隔 = max(15, 35 - int(存活秒 // 5))
            基礎速度 = 3 + int(存活秒 // 10)

        # ===== 繪圖 =====
        螢幕.fill((12, 12, 28))

        # 背景星星
        for _ in range(60):
            sx = (int(存活秒 * 17 + _ * 137) if 手已偵測 else _ * 137) % 寬
            sy = (int(存活秒 * 7 + _ * 211) if 手已偵測 else _ * 211) % 高
            亮度 = 60 + ((int(存活秒) + _ * 3) % 5) * 30
            pygame.draw.circle(螢幕, (亮度, 亮度, 亮度 + 20), (sx, sy), 1)

        # 隕石
        for m in 隕石列表:
            c = m["rect"].center
            r = m["rect"].width // 2
            色 = (160 + (m["rect"].width % 40), 70 + (m["rect"].width % 30), 40)
            pygame.draw.circle(螢幕, 色, c, r)
            pygame.draw.circle(螢幕, (色[0] - 40, 色[1] - 20, 色[2] - 10),
                             (c[0] - r // 3, c[1] - r // 3), r // 4)
            pygame.draw.circle(螢幕, (色[0] + 20, 色[1] + 10, 色[2]),
                             (c[0] + r // 4, c[1] + r // 4), r // 5)

        # 子彈
        for b in 子彈列表:
            pygame.draw.rect(螢幕, (255, 240, 80), b)
            pygame.draw.rect(螢幕, (255, 200, 50),
                           (b.x - 1, b.y - 3, b.width + 2, b.height + 6), 1)

        # 彈藥補給
        for p in 補給列表:
            pygame.draw.rect(螢幕, (50, 200, 80), p["rect"], border_radius=5)
            r = p["rect"]
            pygame.draw.rect(螢幕, (220, 255, 220),
                           (r.centerx - 3, r.top + 4, 6, r.height - 8), border_radius=2)

        # 飛船
        if 手已偵測:
            繪製飛船(螢幕, 飛船, 飛行中)

            # 射擊瞄準線
            if not 飛行中 and 彈藥數 > 0:
                pygame.draw.line(螢幕, (255, 255, 100),
                               (飛船.centerx, 飛船.top), (飛船.centerx, 0), 2)

        # ---- 等待手部偵測 ----
        if not 手已偵測:
            提示 = 大字型.render("請將手置於鏡頭前", True, (255, 255, 200))
            螢幕.blit(提示, (寬 // 2 - 提示.get_width() // 2, 高 // 2 - 40))
            副提示 = 字型.render("（偵測到綠色物體後自動開始）", True, (180, 180, 180))
            螢幕.blit(副提示, (寬 // 2 - 副提示.get_width() // 2, 高 // 2 + 20))

        # ---- UI（右上角）----
        if 手已偵測:
            分數表面 = 字型.render(f"分數 {總分}", True, (255, 255, 255))
            螢幕.blit(分數表面, (寬 - 20 - 分數表面.get_width(), 12))
            命表面 = 字型.render(f"命 {'O' * 命}", True, (255, 100, 100))
            螢幕.blit(命表面, (寬 - 20 - 命表面.get_width(), 40))

            彈藥文字 = f"彈藥 {'O' * 彈藥數}{'_' * (最大彈藥 - 彈藥數)}"
            彈藥表面 = 字型.render(彈藥文字, True, (255, 220, 100))
            螢幕.blit(彈藥表面, (寬 - 20 - 彈藥表面.get_width(), 68))

            狀態對照 = {"張手": "飛行中", "握拳": "射擊中"}
            狀態顯示 = 狀態對照.get(手勢, "飛行中")
            if not 飛行中 and 彈藥數 == 0:
                狀態顯示 = "無彈藥"
            狀態表面 = 字型.render(狀態顯示, True, (180, 180, 200))
            螢幕.blit(狀態表面, (寬 - 20 - 狀態表面.get_width(), 96))

            控制表面 = 字型.render("鏡頭", True, (150, 150, 160))
            螢幕.blit(控制表面, (寬 - 20 - 控制表面.get_width(), 124))

        # ---- 鏡頭小畫面（左上角）----
        if 有鏡頭 and 最近frame is not None:
            小畫面 = cv2.resize(最近frame, (160, 120))
            小畫面 = cv2.flip(小畫面, 1)
            小畫面 = cv2.cvtColor(小畫面, cv2.COLOR_BGR2RGB)
            小畫面 = np.transpose(小畫面, (1, 0, 2))
            預覽表面 = pygame.surfarray.make_surface(小畫面)
            螢幕.blit(預覽表面, (10, 10))
            if 比例x is not None:
                dx = int(最後比例x * 160)
                pygame.draw.circle(螢幕, (255, 60, 60),
                                 (10 + dx, 10 + 60), 6)
                pygame.draw.circle(螢幕, (255, 255, 100),
                                 (10 + dx, 10 + 60), 10, 2)
            pygame.draw.rect(螢幕, (100, 100, 100),
                           (9, 9, 162, 122), 1)

        # ---- 結束 + 排行畫面 ----
        if 遊戲結束旗:
            新增排行(玩家名, 總分)
            排行 = 取得今日排行()

            s = pygame.Surface((寬, 高), pygame.SRCALPHA)
            s.fill((0, 0, 0, 200))
            螢幕.blit(s, (0, 0))

            # 標題
            t1 = 大字型.render("遊戲結束", True, (255, 100, 100))
            螢幕.blit(t1, (寬 // 2 - t1.get_width() // 2, 50))

            # 玩家分數
            分數文字 = f"{玩家名}  存活 {存活秒:.1f} 秒  總分 {總分}"
            t2 = 字型.render(分數文字, True, (255, 255, 200))
            螢幕.blit(t2, (寬 // 2 - t2.get_width() // 2, 110))

            # 今日排行
            排行標題 = 大字型.render("今日排行", True, (0, 200, 255))
            螢幕.blit(排行標題, (寬 // 2 - 排行標題.get_width() // 2, 170))

            開始y = 230
            for i, entry in enumerate(排行):
                排名標記 = ["冠軍", "亞軍", "季軍", "第 4 名", "第 5 名"][i]
                是否玩家 = (entry["name"] == 玩家名 and entry["score"] == 總分)
                顏色 = (255, 255, 100) if 是否玩家 else (220, 220, 220)
                字 = 大字型 if 是否玩家 else 小字型
                前墜 = "> " if 是否玩家 else "  "
                排行文字 = f"{前墜}{排名標記}  {entry['name']}  {entry['score']} 分"
                t = 字.render(排行文字, True, 顏色)
                螢幕.blit(t, (寬 // 2 - t.get_width() // 2, 開始y + i * 42))
                if 是否玩家 and i >= 5:
                    # 玩家不在前 5，在後面補顯示
                    pass

            # 如果玩家不在前 5，額外顯示
            玩家在排行 = any(e["name"] == 玩家名 and e["score"] == 總分 for e in 排行)
            if not 玩家在排行:
                名次 = sum(1 for e in 讀取排行() if e.get("date") == datetime.date.today().isoformat() and e["score"] > 總分) + 1
                提示行 = f"你在今日排名第 {名次} 名"
                t = 字型.render(提示行, True, (255, 255, 100))
                螢幕.blit(t, (寬 // 2 - t.get_width() // 2, 開始y + len(排行) * 42 + 10))

            底部 = 字型.render("按任意鍵離開", True, (150, 150, 150))
            螢幕.blit(底部, (寬 // 2 - 底部.get_width() // 2, 高 - 60))

            pygame.display.flip()

            waiting = True
            while waiting:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT or e.type == pygame.KEYDOWN:
                        waiting = False
                        遊戲中 = False
            break

        pygame.display.flip()
        clock.tick(60)

    # ---- 清理 ----
    if 有鏡頭:
        cap.release()
    pygame.quit()
    print(f"遊戲結束，{玩家名} 最終分數：{總分}")


if __name__ == "__main__":
    main()
