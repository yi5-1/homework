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

    def 排除臉部(self, frame, 遮罩):
        """
        臉部也是膚色，YCrCb 色塊偵測常常把臉判定成「最大色塊」蓋過手。
        用 Haar 臉部偵測把臉（含脖子附近）的區域直接從遮罩挖掉，
        縮小圖片做偵測是為了效能（README 有提醒偵測不要太重）。
        """
        if self.臉部偵測器 is None:
            return
        try:
            縮放 = 0.5
            小圖 = cv2.resize(frame, None, fx=縮放, fy=縮放)
            灰階 = cv2.cvtColor(小圖, cv2.COLOR_BGR2GRAY)
            臉部們 = self.臉部偵測器.detectMultiScale(灰階, scaleFactor=1.2, minNeighbors=5, minSize=(40, 40))
            for (fx, fy, fw, fh) in 臉部們:
                fx, fy, fw, fh = int(fx / 縮放), int(fy / 縮放), int(fw / 縮放), int(fh / 縮放)
                pad = int(fh * 0.4)
                x0, y0 = max(0, fx - pad), max(0, fy - pad)
                x1, y1 = min(遮罩.shape[1], fx + fw + pad), min(遮罩.shape[0], fy + fh + int(pad * 1.8))
                遮罩[y0:y1, x0:x1] = 0
        except Exception:
            pass

    def 找色塊中心x(self, frame):
        try:
            frame = cv2.flip(frame, 1)
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            遮罩 = cv2.inRange(ycrcb, self.目標下限, self.目標上限)
            self.排除臉部(frame, 遮罩)
            核心 = np.ones((5, 5), np.uint8)
            遮罩 = cv2.morphologyEx(遮罩, cv2.MORPH_OPEN, 核心)
            遮罩 = cv2.dilate(遮罩, 核心, iterations=2)
            contours, _ = cv2.findContours(遮罩, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None, 1.0, 0
            最大輪廓 = max(contours, key=cv2.contourArea)
            if cv2.contourArea(最大輪廓) < 1500:
                return None, 1.0, 0
            M = cv2.moments(最大輪廓)
            if M["m00"] == 0:
                return None, 1.0, 0
            比例x = M["m10"] / M["m00"] / frame.shape[1]

            # 凸包/凸包缺陷計算容易因為輪廓形狀（自相交、退化輪廓）丟例外，
            # 獨立包一層 try，避免因此連累已經算好的 比例x 一起被丟掉
            固實度 = 1.0
            缺陷數 = 0
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

            return 比例x, 固實度, 缺陷數
        except Exception:
            return None, 1.0, 0

    def 畫手掌(self, lm, w=160, h=120):
        import pygame
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        if lm is None: return surf
        def p(i): return (int((1.0-lm[i].x)*w), int(lm[i].y*h))
        for a,b in self.連線:
            try: pygame.draw.line(surf, (0,255,120), p(a), p(b), 2)
            except Exception: pass
        for i in range(21):
            try: pygame.draw.circle(surf, (255,255,120), p(i), 3)
            except Exception: pass
        return surf

    def update(self, frame):
        if frame is None:
            return {"比例x": None, "手勢": "張手", "固實度值": 1.0, "缺陷數": 0, "手掌疊層": None}
        比例x, 固實度值, 缺陷數 = self.找色塊中心x(frame)
        手勢 = "張手"
        疊層 = None
        if 比例x is None and self.hands is not None:
            try:
                r = self.hands.detect(MpImage(MpImageFormat.SRGB, frame))
                hl = r.hand_landmarks
                if hl:
                    h = hl[0]
                    比例x = 1.0 - h[0].x
                    curled = sum(h[t].y > h[t-2].y for t in [8, 12, 16, 20])
                    if curled >= 3:
                        手勢 = "握拳"
                        固實度值 = 0.86
                        缺陷數 = 0
                    else:
                        手勢 = "張手"
                        固實度值 = 0.5
                        缺陷數 = 2
                    疊層 = self.畫手掌(h)
            except Exception:
                pass
        return {"比例x": 比例x, "手勢": 手勢, "固實度值": 固實度值, "缺陷數": 缺陷數, "手掌疊層": 疊層}
