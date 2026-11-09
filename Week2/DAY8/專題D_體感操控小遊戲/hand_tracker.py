import cv2, numpy as np, os

try:
    from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision.core.image import Image as MpImage, ImageFormat as MpImageFormat
    _有mediapipe = True
except ImportError:
    _有mediapipe = False
    HandLandmarker = HandLandmarkerOptions = RunningMode = BaseOptions = MpImage = MpImageFormat = None


class HandTracker:
    連線 = [
        (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
        (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
        (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17),
    ]

    def __init__(self):
        self.膚色下限 = np.array([0, 133, 77])
        self.膚色上限 = np.array([255, 173, 127])
        self.目標下限 = self.膚色下限.copy()
        self.目標上限 = self.膚色上限.copy()
        self.校色容許誤差 = np.array([0, 18, 18])  # 校色只調 Cr/Cb，Y（亮度）不限制
        self.臉部偵測器 = None
        try:
            路徑 = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
            分類器 = cv2.CascadeClassifier(路徑)
            if not 分類器.empty():
                self.臉部偵測器 = 分類器
        except Exception:
            pass

        self.hands = None
        if _有mediapipe:
            try:
                路徑 = os.path.join(os.path.expanduser("~"), "mediapipe_models", "hand_landmarker.task")
                if os.path.exists(路徑):
                    opts = HandLandmarkerOptions(
                        base_options=BaseOptions(model_asset_path=路徑),
                        running_mode=RunningMode.IMAGE, num_hands=2,
                    )
                    self.hands = HandLandmarker.create_from_options(opts)
            except Exception:
                pass

    def 校色(self, frame, 取樣邊長=30):
        """
        用畫面正中央一小塊當樣本，更新目標 Cr/Cb 範圍（呼叫端負責在預覽畫面正中央
        畫十字準心，引導玩家把手掌對準那裡再按 C）。

        固定的標準膚色範圍（self.膚色上下限）在不同攝影機白平衡、燈光、膚色下常常
        抓不到完整的手——可能只抓到手掌邊緣一小條亮部，這種細長色塊本身幾乎沒有凹陷、
        固實度會很高，於是不管實際手勢是什麼都會被誤判成握拳。校色能讓範圍貼近
        「這台攝影機、這個當下光線」下手掌實際的顏色，抓到完整手掌而不是一條邊。
        回傳 True/False 代表有沒有校色成功。
        """
        try:
            frame = cv2.flip(frame, 1)  # 跟 找色塊中心x 用同一個方向，準心才會對得上
            h, w = frame.shape[:2]
            cx, cy = w // 2, h // 2
            半邊 = 取樣邊長 // 2
            區塊 = frame[max(0, cy - 半邊):cy + 半邊, max(0, cx - 半邊):cx + 半邊]
            if 區塊.size == 0:
                return False
            ycrcb區塊 = cv2.cvtColor(區塊, cv2.COLOR_BGR2YCrCb)
            平均 = ycrcb區塊.reshape(-1, 3).mean(axis=0)
            下限 = np.clip(平均 - self.校色容許誤差, [0, 77, 60], [255, 200, 140]).astype(int)
            上限 = np.clip(平均 + self.校色容許誤差, [0, 77, 60], [255, 200, 140]).astype(int)
            下限[0], 上限[0] = 0, 255  # Y 一律不限制，只鎖色調不鎖亮度
            self.目標下限, self.目標上限 = 下限, 上限
            return True
        except Exception:
            return False

    def 找臉部排除框(self, frame):
        """
        偵測臉部（含一點頸部緩衝），回傳排除框座標列表 [(x0,y0,x1,y1), ...]。

        舊版做法是直接把這個框內的遮罩像素全部清成 0——問題是手舉在臉/下巴附近時
        （體感操作很常見的姿勢）框會跟手的輪廓重疊，於是連手的一部分甚至整塊都被
        一起挖掉，變成「為了排臉反而偵測不到手」。改成只回傳座標、不動遮罩，
        交給 找色塊中心x() 用「輪廓重心是否落在框內」來判斷該不該排除，手只是邊緣
        蹭到框不會被牽連，只有真的整塊落在框內（判斷成臉本身）才會被排除。
        """
        if self.臉部偵測器 is None:
            return []
        try:
            縮放 = 0.5
            小圖 = cv2.resize(frame, None, fx=縮放, fy=縮放)
            灰階 = cv2.cvtColor(小圖, cv2.COLOR_BGR2GRAY)
            臉部們 = self.臉部偵測器.detectMultiScale(灰階, scaleFactor=1.2, minNeighbors=5, minSize=(40, 40))
            框列表 = []
            for (fx, fy, fw, fh) in 臉部們:
                fx, fy, fw, fh = int(fx / 縮放), int(fy / 縮放), int(fw / 縮放), int(fh / 縮放)
                pad = int(fh * 0.4)
                x0, y0 = max(0, fx - pad), max(0, fy - pad)
                x1 = min(frame.shape[1], fx + fw + pad)
                y1 = min(frame.shape[0], fy + fh + int(pad * 1.8))
                框列表.append((x0, y0, x1, y1))
            return 框列表
        except Exception:
            return []

    def 找色塊中心x(self, frame):
        """
        回傳 None（沒找到）或一個 dict：
          比例x / 固實度 / 缺陷數：跟以前一樣，給手勢判斷用。
          中心px / 凸包 / 畫面寬 / 畫面高：新增的幾何資訊，給 畫色塊() 畫「中心點 + 凸包輪廓」
          用，方便直接在預覽畫面上看到偵測到什麼、判斷手勢為什麼不準。
        """
        try:
            frame = cv2.flip(frame, 1)
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            遮罩 = cv2.inRange(ycrcb, self.目標下限, self.目標上限)
            核心 = np.ones((5, 5), np.uint8)
            遮罩 = cv2.morphologyEx(遮罩, cv2.MORPH_OPEN, 核心)
            遮罩 = cv2.dilate(遮罩, 核心, iterations=2)
            contours, _ = cv2.findContours(遮罩, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None

            臉部框列表 = self.找臉部排除框(frame)

            # 在所有候選色塊裡挑「面積最大、且重心不落在臉部框內」的那個，
            # 而不是先挑最大再排臉——這樣即使最大的剛好是臉，還有機會選到次大的手
            最大輪廓 = None
            最大面積 = 0
            for c in contours:
                面積 = cv2.contourArea(c)
                if 面積 < 1500 or 面積 <= 最大面積:
                    continue
                M = cv2.moments(c)
                if M["m00"] == 0:
                    continue
                cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
                是臉 = any(x0 <= cx <= x1 and y0 <= cy <= y1 for (x0, y0, x1, y1) in 臉部框列表)
                if 是臉:
                    continue
                最大輪廓, 最大面積 = c, 面積

            if 最大輪廓 is None:
                return None
            M = cv2.moments(最大輪廓)
            if M["m00"] == 0:
                return None
            中心px = (M["m10"] / M["m00"], M["m01"] / M["m00"])
            比例x = 中心px[0] / frame.shape[1]

            # 凸包/凸包缺陷計算容易因為輪廓形狀（自相交、退化輪廓）丟例外，
            # 獨立包一層 try，避免因此連累已經算好的 比例x 一起被丟掉
            固實度 = 1.0
            缺陷數 = 0
            凸包 = None
            try:
                凸包 = cv2.convexHull(最大輪廓)
                輪廓面積 = cv2.contourArea(最大輪廓)
                凸包面積 = cv2.contourArea(凸包)
                固實度 = 輪廓面積 / 凸包面積 if 凸包面積 > 0 else 1.0
                凸包索引 = cv2.convexHull(最大輪廓, returnPoints=False)
                if 凸包索引 is not None and len(凸包索引) > 3:
                    缺陷 = cv2.convexityDefects(最大輪廓, 凸包索引)
                    if 缺陷 is not None:
                        for i in range(缺陷.shape[0]):
                            s, e, f, d = 缺陷[i, 0]
                            if d / 256.0 > 18:
                                缺陷數 += 1
            except Exception:
                pass

            return {
                "比例x": 比例x, "固實度": 固實度, "缺陷數": 缺陷數,
                "中心px": 中心px, "凸包": 凸包,
                "畫面寬": frame.shape[1], "畫面高": frame.shape[0],
            }
        except Exception:
            return None

    def 畫色塊(self, 色塊, w=160, h=120):
        """
        把顏色偵測的凸包輪廓＋中心點畫成小疊層，疊在鏡頭預覽上，方便debug。
        凸包顏色依照跟遊戲主邏輯同一套門檻（固實度 > 0.85 或 缺陷數 < 2 → 握拳）
        即時反映手勢判斷：黃色＝目前判定握拳，綠色＝張手，方便直接用肉眼確認
        「為什麼這個手勢被判斷成這樣」而不用另外開調參工具。
        """
        import pygame
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        try:
            握拳中 = 色塊.get("固實度", 1.0) > 0.85 and 色塊.get("缺陷數", 0) < 2
            凸包色 = (255, 230, 0) if 握拳中 else (0, 255, 140)
            sx = w / 色塊["畫面寬"]
            sy = h / 色塊["畫面高"]
            凸包 = 色塊.get("凸包")
            if 凸包 is not None and len(凸包) >= 3:
                pts = [(int(p[0][0] * sx), int(p[0][1] * sy)) for p in 凸包]
                pygame.draw.polygon(surf, 凸包色, pts, 2)
            cx, cy = 色塊["中心px"]
            cx, cy = int(cx * sx), int(cy * sy)
            pygame.draw.circle(surf, (255, 60, 60), (cx, cy), 5)
            pygame.draw.circle(surf, (255, 255, 100), (cx, cy), 9, 2)
        except Exception:
            pass
        return surf

    def 畫手掌(self, lm, 握拳中=False, w=160, h=120):
        """MediaPipe 骨架版本，顏色跟 畫色塊() 用同一套規則：握拳黃色、張手綠色。"""
        import pygame
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        if lm is None: return surf
        骨架色 = (255, 230, 0) if 握拳中 else (0, 255, 120)
        def p(i): return (int((1.0-lm[i].x)*w), int(lm[i].y*h))
        for a,b in self.連線:
            try: pygame.draw.line(surf, 骨架色, p(a), p(b), 2)
            except Exception: pass
        for i in range(21):
            try: pygame.draw.circle(surf, (255,255,120), p(i), 3)
            except Exception: pass
        try:
            wx, wy = p(0)
            pygame.draw.circle(surf, (255, 60, 60), (wx, wy), 5)
            pygame.draw.circle(surf, (255, 255, 100), (wx, wy), 9, 2)
        except Exception:
            pass
        return surf

    def update(self, frame):
        if frame is None:
            return {"比例x": None, "手勢": "張手", "固實度值": 1.0, "缺陷數": 0, "手掌疊層": None}

        色塊 = self.找色塊中心x(frame)
        比例x = 色塊["比例x"] if 色塊 is not None else None
        固實度值 = 色塊["固實度"] if 色塊 is not None else 1.0
        缺陷數 = 色塊["缺陷數"] if 色塊 is not None else 0
        手勢 = "張手"
        疊層 = None

        if 色塊 is not None:
            疊層 = self.畫色塊(色塊)
        elif self.hands is not None:
            try:
                r = self.hands.detect(MpImage(MpImageFormat.SRGB, frame))
                hl = r.hand_landmarks
                if hl:
                    h = hl[0]
                    比例x = 1.0 - h[0].x
                    curled = sum(h[t].y > h[t-2].y for t in [8, 12, 16, 20])
                    握拳中 = curled >= 3
                    if 握拳中:
                        手勢 = "握拳"
                        固實度值 = 0.86
                        缺陷數 = 0
                    else:
                        手勢 = "張手"
                        固實度值 = 0.5
                        缺陷數 = 2
                    疊層 = self.畫手掌(h, 握拳中=握拳中)
            except Exception:
                pass

        return {"比例x": 比例x, "手勢": 手勢, "固實度值": 固實度值, "缺陷數": 缺陷數, "手掌疊層": 疊層}
