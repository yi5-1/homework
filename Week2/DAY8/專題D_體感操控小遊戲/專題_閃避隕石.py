import cv2
import numpy as np
import pygame
import random
import datetime
import json
import os
import sys
import traceback

# ===== 設定 =====
# 標準膚色 YCrCb 範圍（電腦視覺教材常見的膚色偵測範圍：Cr∈[133,173], Cb∈[77,127]，
# Y 全開放不限制，因此不特別要求使用者每次都先校色，直接用手就能玩）。
膚色下限 = np.array([0, 133, 77])
膚色上限 = np.array([255, 173, 127])
最小色塊面積 = 2500  # 抓整隻手掌，門檻比抓小物件時要大，避免雜訊誤判
寬, 高 = 800, 600
缺陷深度閾值 = 18
手勢閾值 = 0.85  # 固實度（輪廓面積/凸包面積）高於此值傾向判定為握拳
排行檔案 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ranking.json")

# ===== 狀態常數 =====
ST_姓名, ST_等待, ST_遊戲, ST_結束, ST_離開 = range(5)


# ===== 排行工具（加上例外保護，避免檔案損毀時整個程式當掉）=====
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
        # 檔案損毀或格式錯誤時，不讓遊戲崩潰，當作空排行榜處理
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


# ===== OpenCV 偵測 =====
def 找色塊中心x(frame, 下限, 上限):
    """
    依傳入的 YCrCb 範圍找最大色塊中心（用凸包/凸包缺陷判斷手勢，見 判斷手勢）。
    下限/上限 可在執行期用「現場校色」動態更新（選用），預設即為標準膚色範圍。
    """
    try:
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        遮罩 = cv2.inRange(ycrcb, 下限, 上限)
        # 型態學開/閉運算去除雜訊、補洞：抓膚色時背景常有雜點，這步能讓偵測穩定很多
        遮罩 = cv2.morphologyEx(遮罩, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        遮罩 = cv2.morphologyEx(遮罩, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
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
    except Exception:
        return None, None, 0


def 判斷手勢(固實度, 缺陷數):
    """
    綜合「凸包缺陷數」與「固實度」判斷張手/握拳，回傳 "張手" 或 "握拳"。
    - 缺陷數 >= 2:手指間有明顯凹陷 → 張手
    - 缺陷數 == 0 且固實度偏高（輪廓貼近凸包）→ 握拳
    - 其餘邊界情況（例如過渡動作）以固實度為最終依據
    """
    if 缺陷數 >= 2:
        return "張手"
    if 缺陷數 == 0 and 固實度 > 手勢閾值:
        return "握拳"
    return "握拳" if 固實度 > 手勢閾值 else "張手"


# ===== 現場校色（選用：預設膚色範圍不準時才需要）=====
校色容許誤差 = np.array([0, 15, 15])  # 只微調 Cr/Cb，Y 仍不限制

def 取樣中心色(frame, 取樣邊長=30):
    """
    取畫面正中央一小塊區域的平均 YCrCb，回傳 (下限, 上限)。
    用在「把手掌對準準心後按 C」的現場校色功能（選用），
    光線特殊、預設範圍不準時可用來微調。
    """
    try:
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        半邊 = 取樣邊長 // 2
        區塊 = frame[max(0, cy - 半邊):cy + 半邊, max(0, cx - 半邊):cx + 半邊]
        if 區塊.size == 0:
            return None
        ycrcb區塊 = cv2.cvtColor(區塊, cv2.COLOR_BGR2YCrCb)
        平均 = ycrcb區塊.reshape(-1, 3).mean(axis=0)
        下限 = np.clip(平均 - 校色容許誤差, [0, 77, 60], [255, 200, 140]).astype(int)
        上限 = np.clip(平均 + 校色容許誤差, [0, 77, 60], [255, 200, 140]).astype(int)
        下限[0], 上限[0] = 0, 255  # Y 一律不限制
        return 下限, 上限
    except Exception:
        return None


# ===== 開啟攝影機（跨平台）=====
def 開啟攝影機():
    """
    Windows 下優先嘗試 DirectShow 後端（較不易卡在初始化），
    其他平台一律用預設後端，避免 CAP_DSHOW 在 Linux/Mac 上開不了機。
    """
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
    return None  # 明確回傳 None，避免殘留「開啟失敗」的物件被誤判為「有鏡頭」


# ===== 字型（容錯：依序嘗試常見中文字型，找不到才退回系統預設）=====
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
    # 都找不到就用系統預設字型（可能無法正確顯示中文，但至少不會崩潰）
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

    # 姓名輸入框位置（固定，drawing 與 IME 候選窗定位都用同一份座標）
    輸入框範圍 = pygame.Rect(寬 // 2 - 150, 高 // 2 - 25, 300, 50)

    # 明確啟動文字輸入模式，並告訴系統輸入法候選窗要顯示在哪裡。
    # 修正：中文輸入法（IME）組字時只會送出 TEXTINPUT 事件（不會有對應的
    # KEYDOWN + unicode），如果沒有正確啟動/定位文字輸入模式，某些系統上
    # 中文組字會顯示錯位甚至完全收不到，導致「中文打不出來」。
    pygame.key.start_text_input()
    pygame.key.set_text_input_rect(輸入框範圍)

    # ---- 開啟攝影機 ----
    cap = 開啟攝影機()
    有鏡頭 = cap is not None
    if not 有鏡頭:
        print("[提示] 找不到可用的攝影機，將以無鏡頭模式執行（無法偵測手部位置）。")

    # 目前使用的偵測顏色範圍（可用「現場校色」動態更新，預設為膚色）
    目標下限 = 膚色下限.copy()
    目標上限 = 膚色上限.copy()
    最近偵測到 = False  # 給預覽框顯示「已偵測 / 未偵測」用

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
    彈藥數 = 0
    最大彈藥 = 3
    補給倒數 = 0
    補給間隔 = 150
    開始時間 = 0
    比例x = None
    手勢 = "張手"
    固實度值 = None
    缺陷數 = 0
    最新遮罩 = None

    # ---- 暖幀 ----
    最近frame = None
    if 有鏡頭:
        for _ in range(15):
            cap.read()

    # ---- 輔助：鏡頭預覽（遮罩永遠疊在上面，看 HSV 抓到什麼）----
    def 更新預覽(螢幕, frame, 偵測x, 遮罩, 顯示校色準心=False):
        if frame is None:
            return
        try:
            f = cv2.flip(frame, 1)
            f = cv2.resize(f, (160, 120))
            f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            表面 = pygame.image.frombuffer(f.tobytes(), (160, 120), "RGB")
            if 遮罩 is not None:
                try:
                    m = cv2.resize(遮罩, (160, 120))
                    m = cv2.cvtColor(m, cv2.COLOR_GRAY2RGB)
                    m = m.astype(np.float32) * 0.40
                    疊層 = np.clip(f.astype(np.float32) * 0.60 + m, 0, 255).astype(np.uint8)
                    表面 = pygame.image.frombuffer(疊層.tobytes(), (160, 120), "RGB")
                except Exception:
                    pass
            螢幕.blit(表面, (10, 10))
            偵測到 = 偵測x is not None
            if 偵測到:
                dx = int(偵測x * 160)
                pygame.draw.circle(螢幕, (255, 60, 60), (10 + dx, 70), 6)
                pygame.draw.circle(螢幕, (255, 255, 100), (10 + dx, 70), 10, 2)
            if 顯示校色準心:
                ccx, ccy = 10 + 80, 10 + 60
                pygame.draw.line(螢幕, (0, 220, 255), (ccx - 10, ccy), (ccx + 10, ccy), 1)
                pygame.draw.line(螢幕, (0, 220, 255), (ccx, ccy - 10), (ccx, ccy + 10), 1)
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

            # ---- 偵測（共用）----
            if ret and frame is not None:
                try:
                    比例x, 固實度值, 缺陷數 = 找色塊中心x(frame, 目標下限, 目標上限)
                except Exception:
                    比例x = None
            else:
                比例x = None
            最近偵測到 = 比例x is not None

            # ---- 事件：每格只讀一次，所有狀態共用同一份清單 ----
            # （修正原本 bug：外層已清空佇列，各狀態分支再讀一次只會拿到空清單，
            #   導致 ST_姓名 狀態收不到事件，姓名打不了字）
            事件清單 = pygame.event.get()
            for e in 事件清單:
                if e.type == pygame.QUIT:
                    狀態 = ST_離開

            # 現場校色（僅在「等待舉手」畫面生效，避免和姓名輸入時打字的 C 鍵衝突）
            if 狀態 == ST_等待:
                for e in 事件清單:
                    if e.type == pygame.KEYDOWN and e.key == pygame.K_c and 最近frame is not None:
                        結果 = 取樣中心色(最近frame)
                        if 結果 is not None:
                            目標下限, 目標上限 = 結果
                            print(f"[校色] 已更新偵測範圍 下限={目標下限} 上限={目標上限}")

            # ===== 狀態：姓名輸入 =====
            if 狀態 == ST_姓名:
                # 這一格是否有收到 TEXTINPUT 事件：
                # 一般打字（含中文輸入法組字完成後）都會送出 TEXTINPUT，內容已經是
                # 組好的完整文字（例如中文），這裡優先採用；只有在完全沒有收到
                # TEXTINPUT 時，才退回用 KEYDOWN 的 e.unicode 當備援（例如英數字），
                # 避免兩種事件同時處理導致同一個字被打兩次。
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

                # 注意：本狀態刻意「不」偵測手部跳過輸入 ——
                # 使用者要求「先輸入完姓名（按 Enter）才能進入舉手畫面」，
                # 不是「輸入姓名 或 舉手」兩者擇一即可跳過。

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
                更新預覽(螢幕, 最近frame, 比例x if 比例x is not None else None, 最新遮罩)

            # ===== 狀態：等待手部（姓名已確認）=====
            elif 狀態 == ST_等待:
                玩家名 = 輸入姓名 if 輸入姓名 else "玩家"

                if 有鏡頭:
                    if 比例x is not None:
                        狀態 = ST_遊戲
                        開始時間 = pygame.time.get_ticks()
                        手勢 = "張手"
                        飛行中 = True
                else:
                    # 無鏡頭時允許按空白鍵直接開始（鍵盤備用模式）
                    for e in 事件清單:
                        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                            狀態 = ST_遊戲
                            開始時間 = pygame.time.get_ticks()
                            手勢 = "張手"
                            飛行中 = True

                螢幕.fill((12, 12, 28))
                畫星星()
                畫等待()
                if 有鏡頭:
                    校色提示 = 字型.render("預設膚色不準？按 C 對準左上角準心微調（選用）", True, (120, 200, 255))
                    螢幕.blit(校色提示, (寬 // 2 - 校色提示.get_width() // 2, 高 // 2 + 60))
                更新預覽(螢幕, 最近frame, 比例x if 比例x is not None else None, 最新遮罩, 顯示校色準心=True)

            # ===== 狀態：遊戲中 =====
            elif 狀態 == ST_遊戲:
                # 手勢判斷（與獨立的手掌開合偵測腳本共用同一套邏輯）
                if 比例x is not None:
                    最後比例x = 比例x
                    手勢 = 判斷手勢(固實度值, 缺陷數)
                elif not 有鏡頭:
                    # 無鏡頭備援：左右鍵移動、空白鍵切換射擊
                    鍵 = pygame.key.get_pressed()
                    if 鍵[pygame.K_LEFT]:
                        最後比例x = max(0.0, 最後比例x - 0.02)
                    if 鍵[pygame.K_RIGHT]:
                        最後比例x = min(1.0, 最後比例x + 0.02)
                    手勢 = "握拳" if 鍵[pygame.K_SPACE] else "張手"

                飛行中 = (手勢 == "張手")
                now = pygame.time.get_ticks()
                存活ms = now - 開始時間
                存活秒 = 存活ms / 1000.0
                總分 = int(存活ms // 10)

                if 飛行中:
                    if 比例x is not None:
                        飛船.centerx = int(比例x * 寬)
                    elif not 有鏡頭:
                        飛船.centerx = int(最後比例x * 寬)
                    飛船.clamp_ip(螢幕.get_rect())

                if not 飛行中:
                    if 連射延遲 <= 0 and 彈藥數 > 0:
                        子彈列表.append(pygame.Rect(飛船.centerx - 3, 飛船.top - 5, 6, 18))
                        彈藥數 -= 1
                        連射延遲 = 12
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
                更新預覽(螢幕, 最近frame, 最後比例x, 最新遮罩)

            # ===== 狀態：結束 + 排行 =====
            elif 狀態 == ST_結束:
                新增排行(玩家名, 總分)
                排行 = 今日排行()

                s = pygame.Surface((寬, 高), pygame.SRCALPHA)
                s.fill((0, 0, 0, 200))
                螢幕.blit(s, (0, 0))
                t1 = 大字型.render("遊戲結束", True, (255, 100, 100))
                螢幕.blit(t1, (寬 // 2 - t1.get_width() // 2, 50))
                t2 = 字型.render(f"{玩家名}  存活 {存活秒:.1f} 秒  總分 {總分}", True, (255, 255, 200))
                螢幕.blit(t2, (寬 // 2 - t2.get_width() // 2, 110))
                t3 = 大字型.render("今日排行", True, (0, 200, 255))
                螢幕.blit(t3, (寬 // 2 - t3.get_width() // 2, 170))
                排名文字 = ["冠軍", "亞軍", "季軍", "第 4 名", "第 5 名"]
                for i, entry in enumerate(排行):
                    是否 = (entry.get("name") == 玩家名 and entry.get("score") == 總分)
                    c = (255, 255, 100) if 是否 else (220, 220, 220)
                    f = 大字型 if 是否 else 小字型
                    txt = f"{'>' if 是否 else ' '}{排名文字[i]}  {entry.get('name')}  {entry.get('score')} 分"
                    t = f.render(txt, True, c)
                    螢幕.blit(t, (寬 // 2 - t.get_width() // 2, 230 + i * 42))
                if not any(e.get("name") == 玩家名 and e.get("score") == 總分 for e in 排行):
                    名次 = sum(1 for e in 讀取排行()
                               if e.get("date") == datetime.date.today().isoformat() and e.get("score", 0) > 總分) + 1
                    t = 字型.render(f"你在今日排名第 {名次} 名", True, (255, 255, 100))
                    螢幕.blit(t, (寬 // 2 - t.get_width() // 2, 230 + len(排行) * 42 + 10))
                底部 = 字型.render("按任意鍵離開", True, (150, 150, 150))
                螢幕.blit(底部, (寬 // 2 - 底部.get_width() // 2, 高 - 60))
                pygame.display.flip()

                # 等待離場
                waiting = True
                while waiting:
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT or e.type == pygame.KEYDOWN:
                            waiting = False
                            狀態 = ST_離開
                    clock.tick(30)

            if 狀態 != ST_離開 and 狀態 != ST_結束:
                pygame.display.flip()
                clock.tick(60)

    except Exception as e:
        print("=" * 50)
        print("[!] 發生未預期錯誤：")
        traceback.print_exc()
        print("=" * 50)
        # 嘗試在 pygame 上顯示錯誤
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
    pygame.quit()
    print(f"遊戲結束，{玩家名} 最終分數：{總分}")


if __name__ == "__main__":
    main()
