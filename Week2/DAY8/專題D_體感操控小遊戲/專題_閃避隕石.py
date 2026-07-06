import cv2
import numpy as np
import pygame
import random
import datetime
import json
import os
import threading
import traceback

from hand_tracker import HandTracker
import 線上排行榜

# ===== 設定 =====
寬, 高 = 800, 600
排行檔案 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ranking.json")

# ===== 狀態常數 =====
ST_姓名, ST_等待, ST_遊戲, ST_結束, ST_離開 = range(5)


# ===== 排行工具 =====
def 讀取排行():
    if not os.path.exists(排行檔案):
        return []
    try:
        with open(排行檔案, "r", encoding="utf-8") as f:
            資料 = json.load(f)
        if not isinstance(資料, list):
            return []
        return 資料
    except Exception:
        return []


def 儲存排行(資料):
    try:
        暫存檔 = 排行檔案 + ".tmp"
        with open(暫存檔, "w", encoding="utf-8") as f:
            json.dump(資料, f, ensure_ascii=False, indent=2)
        os.replace(暫存檔, 排行檔案)
    except Exception:
        traceback.print_exc()


def 今日排行():
    全部 = 讀取排行()
    今日 = datetime.date.today().isoformat()
    今日資料 = [e for e in 全部 if e.get("date") == 今日]
    今日資料.sort(key=lambda e: e.get("score", 0), reverse=True)
    return 今日資料[:5]


def 新增排行(name, score):
    全部 = 讀取排行()
    全部.append({"name": name, "score": score, "date": datetime.date.today().isoformat()})
    儲存排行(全部)


# ===== 開啟攝影機（跨平台）=====
def 開啟攝影機():
    候選後端 = [cv2.CAP_DSHOW, cv2.CAP_ANY] if os.name == "nt" else [cv2.CAP_ANY]
    for backend in 候選後端:
        for idx in range(2):
            cap = None
            try:
                cap = cv2.VideoCapture(idx, backend)
                if cap.isOpened():
                    return cap
                cap.release()
            except Exception:
                if cap is not None:
                    try:
                        cap.release()
                    except Exception:
                        pass
    return None


# ===== 字型 =====
def 選字型(size):
    候選字型名 = [
        "Microsoft JhengHei", "Microsoft JhengHei UI",
        "PingFang TC", "PingFang SC",
        "Noto Sans CJK TC", "Noto Sans CJK SC", "Noto Sans TC",
        "SimHei", "Arial Unicode MS",
    ]
    for 名稱 in 候選字型名:
        try:
            路徑 = pygame.font.match_font(名稱)
            if 路徑:
                return pygame.font.Font(路徑, size)
        except Exception:
            continue
    return pygame.font.SysFont(None, size)


# ===== 遊戲主函式 =====
def main():
    pygame.init()
    螢幕 = pygame.display.set_mode((寬, 高))
    pygame.display.set_caption("體感閃避隕石")
    clock = pygame.time.Clock()
    字型 = 選字型(26)
    大字型 = 選字型(48)
    小字型 = 選字型(22)

    輸入框範圍 = pygame.Rect(寬 // 2 - 150, 高 // 2 - 25, 300, 50)

    pygame.key.start_text_input()
    pygame.key.set_text_input_rect(輸入框範圍)

    # ---- 開啟攝影機 ----
    cap = 開啟攝影機()
    有鏡頭 = cap is not None
    if not 有鏡頭:
        print("[提示] 找不到可用的攝影機，將以無鏡頭模式執行（無法偵測手部位置）。")

    # ---- HandTracker ----
    tracker = HandTracker()

    # ---- 遊戲狀態 ----
    玩家名 = ""
    總分 = 0
    命 = 3
    存活秒 = 0.0
    飛船 = pygame.Rect(寬 // 2 - 25, 高 - 70, 50, 30)
    飛行中 = True
    最後比例x = 0.5
    隕石列表 = []
    子彈列表 = []
    補給列表 = []
    隕石倒數 = 0
    隕石間隔 = 35
    基礎速度 = 3
    連射延遲 = 0
    上次手勢 = "張手"
    彈藥數 = 0
    最大彈藥 = 3
    補給倒數 = 0
    補給間隔 = 150
    開始時間 = 0
    最新手掌疊層 = None

    # ---- 暖幀 ----
    最近frame = None
    if 有鏡頭:
        for _ in range(15):
            cap.read()

    # ---- 輔助：鏡頭預覽 ----
    def 更新預覽(螢幕, frame, 偵測x, 手掌疊層=None):
        if frame is None:
            return
        try:
            f = cv2.flip(frame, 1)
            f = cv2.resize(f, (160, 120))
            f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            表面 = pygame.image.frombuffer(f.tobytes(), (160, 120), "RGB")

            if 手掌疊層 is not None:
                try:
                    疊層 = pygame.Surface((160, 120), pygame.SRCALPHA)
                    疊層.fill((0, 0, 0, 80))
                    疊層.blit(手掌疊層, (0, 0))
                    表面 = 表面.convert_alpha()
                    表面.blit(疊層, (0, 0))
                except Exception:
                    pass

            螢幕.blit(表面, (10, 10))
            偵測到 = 偵測x is not None
            if 偵測到:
                dx = int(偵測x * 160)
                pygame.draw.circle(螢幕, (255, 60, 60), (10 + dx, 70), 6)
                pygame.draw.circle(螢幕, (255, 255, 100), (10 + dx, 70), 10, 2)
            框色 = (60, 220, 100) if 偵測到 else (120, 120, 120)
            pygame.draw.rect(螢幕, 框色, (9, 9, 162, 122), 2)
            狀態文字 = "已偵測" if 偵測到 else "未偵測"
            狀態色 = (60, 255, 120) if 偵測到 else (200, 200, 200)
            s = 小字型.render(狀態文字, True, 狀態色)
            螢幕.blit(s, (10, 135))
        except Exception:
            pass

    # ---- 輔助：背景星星 ----
    def 畫星星(偏移=0):
        for i in range(60):
            sx = (i * 137 + int(偏移 * 17)) % 寬
            sy = (i * 211 + int(偏移 * 7)) % 高
            亮 = 60 + ((int(偏移) + i * 3) % 5) * 30
            pygame.draw.circle(螢幕, (亮, 亮, 亮 + 20), (sx, sy), 1)

    # ---- 輔助：右上 UI ----
    def 畫UI(分數, 命數, 彈藥, 飛行, 手):
        def 靠右(文字, y, 色=(255, 255, 255), 字=字型):
            s = 字.render(文字, True, 色)
            螢幕.blit(s, (寬 - 20 - s.get_width(), y))
        靠右(f"分數 {分數}", 12)
        靠右(f"命 {'O' * 命數}", 40, (255, 100, 100))
        靠右(f"彈藥 {'O' * 彈藥}{'_' * (最大彈藥 - 彈藥)}", 68, (255, 220, 100))
        狀態文字 = {"張手": "飛行中", "握拳": "射擊中"}.get(手, "飛行中")
        if not 飛行 and 彈藥 == 0:
            狀態文字 = "無彈藥"
        靠右(狀態文字, 96, (180, 180, 200))
        if not 有鏡頭:
            靠右("無鏡頭（鍵盤模式）", 124, (255, 160, 90))
        else:
            靠右("鏡頭", 124, (150, 150, 160))

    # ---- 輔助：等待手部 ----
    def 畫等待():
        提示 = "請將手置於鏡頭前" if 有鏡頭 else "無鏡頭，按空白鍵開始"
        t = 大字型.render(提示, True, (255, 255, 200))
        螢幕.blit(t, (寬 // 2 - t.get_width() // 2, 高 // 2 - 40))
        if 有鏡頭:
            t2 = 字型.render("（偵測到手掌後自動開始）", True, (180, 180, 180))
            螢幕.blit(t2, (寬 // 2 - t2.get_width() // 2, 高 // 2 + 20))

    # ===== 狀態機主迴圈 =====
    狀態 = ST_姓名
    輸入姓名 = ""

    try:
        while 狀態 != ST_離開:
            # ---- 讀鏡頭（所有狀態共用）----
            ret = False
            frame = None
            if 有鏡頭:
                try:
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        最近frame = frame.copy()
                except Exception:
                    ret = False
                    frame = None

            # ---- HandTracker 偵測 ----
            最新手掌疊層 = None
            比例x = None
            手勢 = "張手"
            if ret and frame is not None:
                td = tracker.update(frame)
                比例x = td["比例x"]
                手勢 = td["手勢"]
                固實度值 = td.get("固實度值", 1.0)
                缺陷數 = td.get("缺陷數", 0)
                最新手掌疊層 = td["手掌疊層"]
            最近偵測到 = 比例x is not None

            # ---- 事件 ----
            事件清單 = pygame.event.get()
            for e in 事件清單:
                if e.type == pygame.QUIT:
                    狀態 = ST_離開

            # ===== 狀態：姓名輸入 =====
            if 狀態 == ST_姓名:
                有文字輸入事件 = any(e.type == pygame.TEXTINPUT for e in 事件清單)
                for e in 事件清單:
                    if e.type == pygame.TEXTINPUT:
                        if len(輸入姓名) < 12:
                            輸入姓名 += e.text
                    elif e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_RETURN:
                            玩家名 = 輸入姓名 if 輸入姓名 else "玩家"
                            狀態 = ST_等待
                        elif e.key == pygame.K_BACKSPACE:
                            輸入姓名 = 輸入姓名[:-1]
                        elif e.key == pygame.K_ESCAPE:
                            狀態 = ST_離開
                        elif (not 有文字輸入事件) and hasattr(e, "unicode") and e.unicode \
                                and e.unicode.isprintable() and len(輸入姓名) < 12:
                            輸入姓名 += e.unicode

                螢幕.fill((12, 12, 28))
                畫星星()
                t = 大字型.render("體感閃避隕石", True, (0, 180, 255))
                螢幕.blit(t, (寬 // 2 - t.get_width() // 2, 高 // 2 - 120))
                提示 = 字型.render("請輸入姓名後按 Enter 確認", True, (200, 200, 200))
                螢幕.blit(提示, (寬 // 2 - 提示.get_width() // 2, 高 // 2 - 70))
                pygame.draw.rect(螢幕, (50, 50, 70), 輸入框範圍, border_radius=6)
                pygame.draw.rect(螢幕, (0, 180, 255), 輸入框範圍, 2, border_radius=6)
                游標 = "|" if pygame.time.get_ticks() % 1000 < 500 else ""
                ts = 字型.render(輸入姓名 + 游標, True, (255, 255, 255))
                螢幕.blit(ts, (輸入框範圍.x + 10, 輸入框範圍.y + (輸入框範圍.height - ts.get_height()) // 2))
                更新預覽(螢幕, 最近frame, 比例x if 比例x is not None else None, 手掌疊層=最新手掌疊層)

            # ===== 狀態：等待手部（姓名已確認）=====
            elif 狀態 == ST_等待:
                玩家名 = 輸入姓名 if 輸入姓名 else "玩家"

                if 有鏡頭:
                    if 比例x is not None:
                        狀態 = ST_遊戲
                        開始時間 = pygame.time.get_ticks()
                        手勢 = "張手"
                        上次手勢 = "張手"
                        飛行中 = True
                else:
                    for e in 事件清單:
                        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                            狀態 = ST_遊戲
                            開始時間 = pygame.time.get_ticks()
                            手勢 = "張手"
                            上次手勢 = "張手"
                            飛行中 = True

                螢幕.fill((12, 12, 28))
                畫星星()
                畫等待()
                更新預覽(螢幕, 最近frame, 比例x if 比例x is not None else None, 手掌疊層=最新手掌疊層)

            # ===== 狀態：遊戲中 =====
            elif 狀態 == ST_遊戲:
                # ===== 飛船位置核心同步（手動，飛船就動） =====
                if 比例x is not None:
                    最後比例x = 最後比例x * 0.8 + 比例x * 0.2
                elif not 有鏡頭:
                    鍵 = pygame.key.get_pressed()
                    if 鍵[pygame.K_LEFT]: 最後比例x = max(0.0, 最後比例x - 0.02)
                    if 鍵[pygame.K_RIGHT]: 最後比例x = min(1.0, 最後比例x + 0.02)

                飛船.centerx = int(最後比例x * 寬)
                飛船.clamp_ip(螢幕.get_rect())

                # ===== 手勢判斷（純粹拿來開火，不卡移動） =====
                if 比例x is not None:
                    if 固實度值 > 0.85 or 缺陷數 < 2:
                        手勢 = "握拳"
                    else:
                        手勢 = "張手"
                elif not 有鏡頭:
                    手勢 = "握拳" if 鍵[pygame.K_SPACE] else "張手"

                飛行中 = (手勢 == "張手")
                now = pygame.time.get_ticks()
                存活ms = now - 開始時間
                存活秒 = 存活ms / 1000.0
                總分 = int(存活ms // 10)

                # 握拳「這一瞬間」（從張手變握拳）才發射一發，手勢閃爍時靠冷卻避免誤連發
                if 手勢 == "握拳" and 上次手勢 == "張手" and 連射延遲 <= 0 and 彈藥數 > 0:
                    子彈列表.append(pygame.Rect(飛船.centerx - 3, 飛船.top - 5, 6, 18))
                    彈藥數 -= 1
                    連射延遲 = 10
                上次手勢 = 手勢
                連射延遲 -= 1

                # 隕石
                隕石倒數 += 1
                if 隕石倒數 >= 隕石間隔:
                    隕石倒數 = 0
                    大小 = random.randint(22, 52)
                    隕石列表.append({
                        "rect": pygame.Rect(random.randint(0, 寬 - 大小), -大小, 大小, 大小),
                        "vx": random.randint(-2, 2),
                        "vy": 基礎速度 + random.randint(0, 3),
                    })

                # 補給
                補給倒數 += 1
                if 補給倒數 >= 補給間隔 and 彈藥數 < 最大彈藥:
                    補給倒數 = 0
                    x = random.randint(0, 寬 - 22)
                    補給列表.append({"rect": pygame.Rect(x, -22, 22, 22), "vy": 2.5})

                # 更新
                for m in 隕石列表[:]:
                    m["rect"].x += m["vx"]
                    m["rect"].y += m["vy"]
                    if m["rect"].top > 高 + 20 or m["rect"].left < -60 or m["rect"].right > 寬 + 60:
                        隕石列表.remove(m)
                        continue
                    if m["rect"].colliderect(飛船):
                        命 -= 1
                        隕石列表.remove(m)
                        if 命 <= 0:
                            狀態 = ST_結束
                        continue

                for b in 子彈列表[:]:
                    b.y -= 10
                    if b.bottom < 0:
                        子彈列表.remove(b)
                        continue
                    for m in 隕石列表[:]:
                        if b.colliderect(m["rect"]):
                            子彈列表.remove(b)
                            隕石列表.remove(m)
                            break

                for p in 補給列表[:]:
                    p["rect"].y += p["vy"]
                    if p["rect"].top > 高:
                        補給列表.remove(p)
                        continue
                    if p["rect"].colliderect(飛船) and 彈藥數 < 最大彈藥:
                        彈藥數 += 1
                        補給列表.remove(p)

                隕石間隔 = max(15, 35 - int(存活秒 // 5))
                基礎速度 = 3 + int(存活秒 // 10)

                # 繪圖
                螢幕.fill((12, 12, 28))
                畫星星(存活秒)
                for m in 隕石列表:
                    c = m["rect"].center
                    r = m["rect"].width // 2
                    色 = (160 + (m["rect"].width % 40), 70 + (m["rect"].width % 30), 40)
                    pygame.draw.circle(螢幕, 色, c, r)
                    pygame.draw.circle(螢幕, (色[0] - 40, 色[1] - 20, 色[2] - 10), (c[0] - r // 3, c[1] - r // 3), r // 4)
                for b in 子彈列表:
                    pygame.draw.rect(螢幕, (255, 240, 80), b)
                for p in 補給列表:
                    pygame.draw.rect(螢幕, (50, 200, 80), p["rect"], border_radius=5)
                    pygame.draw.rect(螢幕, (220, 255, 220), (p["rect"].centerx - 3, p["rect"].top + 4, 6, p["rect"].height - 8), border_radius=2)
                # 飛船
                pygame.draw.polygon(螢幕, (0, 180, 255), [
                    (飛船.centerx, 飛船.top), (飛船.left, 飛船.bottom - 5), (飛船.right, 飛船.bottom - 5)])
                if 飛行中:
                    火焰長 = 10 + int(8 * np.sin(now * 0.01))
                    pygame.draw.polygon(螢幕, (255, 180, 50), [
                        (飛船.centerx - 8, 飛船.bottom - 5), (飛船.centerx + 8, 飛船.bottom - 5),
                        (飛船.centerx, 飛船.bottom - 5 + 火焰長)])
                if not 飛行中 and 彈藥數 > 0:
                    pygame.draw.line(螢幕, (255, 255, 100), (飛船.centerx, 飛船.top), (飛船.centerx, 0), 2)
                畫UI(總分, 命, 彈藥數, 飛行中, 手勢)
                更新預覽(螢幕, 最近frame, 最後比例x, 手掌疊層=最新手掌疊層)

            # ===== 狀態：結束 + 排行 =====
            elif 狀態 == ST_結束:
                新增排行(玩家名, 總分)  # 本機備份，專題 B 的線上服務沒開時當退路

                # ---- 對接專題 B（多人網頁排行榜）----
                # 送分數 / 取排行榜 是網路呼叫，B 的服務沒開時「連不上」在這台機器上
                # 實測不會馬上失敗、反而會卡到 timeout（見開發過程），丟進背景執行緒跑，
                # 畫面先用本機排行榜秒開，線上資料回來了再自動換成線上榜，避免整個遊戲卡住。
                線上狀態 = {"榜": None}

                def _背景同步線上排行榜(name=玩家名, score=總分, 狀態槽=線上狀態):
                    線上排行榜.送分數(name, score)
                    狀態槽["榜"] = 線上排行榜.取得線上排行榜() or []

                threading.Thread(target=_背景同步線上排行榜, daemon=True).start()

                def 畫結束畫面():
                    線上榜 = 線上狀態["榜"]
                    if 線上榜:
                        排行 = [{"name": e.get("name"), "score": e.get("kills", 0)} for e in 線上榜[:5]]
                        排行標題 = "線上排行榜"
                    else:
                        排行 = 今日排行()
                        排行標題 = "今日排行（本機）"

                    s = pygame.Surface((寬, 高), pygame.SRCALPHA)
                    s.fill((0, 0, 0, 200))
                    螢幕.blit(s, (0, 0))
                    t1 = 大字型.render("遊戲結束", True, (255, 100, 100))
                    螢幕.blit(t1, (寬 // 2 - t1.get_width() // 2, 50))
                    t2 = 字型.render(f"{玩家名}  存活 {存活秒:.1f} 秒  總分 {總分}", True, (255, 255, 200))
                    螢幕.blit(t2, (寬 // 2 - t2.get_width() // 2, 110))
                    t3 = 大字型.render(排行標題, True, (0, 200, 255))
                    螢幕.blit(t3, (寬 // 2 - t3.get_width() // 2, 170))
                    排名文字 = ["冠軍", "亞軍", "季軍", "第 4 名", "第 5 名"]
                    for i, entry in enumerate(排行):
                        是否 = (entry.get("name") == 玩家名 and entry.get("score") == 總分)
                        c = (255, 255, 100) if 是否 else (220, 220, 220)
                        f = 大字型 if 是否 else 小字型
                        txt = f"{'>' if 是否 else ' '}{排名文字[i]}  {entry.get('name')}  {entry.get('score')} 分"
                        t = f.render(txt, True, c)
                        螢幕.blit(t, (寬 // 2 - t.get_width() // 2, 230 + i * 42))
                    if not 線上榜 and not any(e.get("name") == 玩家名 and e.get("score") == 總分 for e in 排行):
                        名次 = sum(1 for e in 讀取排行()
                                  if e.get("date") == datetime.date.today().isoformat() and e.get("score", 0) > 總分) + 1
                        t = 字型.render(f"你在今日排名第 {名次} 名", True, (255, 255, 100))
                        螢幕.blit(t, (寬 // 2 - t.get_width() // 2, 230 + len(排行) * 42 + 10))
                    底部 = 字型.render("按任意鍵離開", True, (150, 150, 150))
                    螢幕.blit(底部, (寬 // 2 - 底部.get_width() // 2, 高 - 60))
                    pygame.display.flip()

                畫結束畫面()

                waiting = True
                while waiting:
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT or e.type == pygame.KEYDOWN:
                            waiting = False
                            狀態 = ST_離開
                    畫結束畫面()  # 持續重繪：線上排行榜背景執行緒一回來畫面就會自動換上
                    clock.tick(30)

            if 狀態 != ST_離開 and 狀態 != ST_結束:
                pygame.display.flip()
                clock.tick(60)

    except Exception as e:
        print("=" * 50)
        print("[!] 發生未預期錯誤：")
        traceback.print_exc()
        print("=" * 50)
        try:
            螢幕.fill((0, 0, 0))
            err = 字型.render(f"錯誤：{e}", True, (255, 100, 100))
            螢幕.blit(err, (20, 高 // 2))
            pygame.display.flip()
            pygame.time.wait(5000)
        except Exception:
            pass

    # ---- 清理 ----
    if cap is not None:
        try:
            cap.release()
        except Exception:
            pass
    if tracker.hands is not None:
        try:
            tracker.hands.close()
        except Exception:
            pass
    pygame.quit()
    print(f"遊戲結束，{玩家名} 最終分數：{總分}")


if __name__ == "__main__":
    main()
