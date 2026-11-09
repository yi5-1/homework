import cv2
import threading
import time


class CameraStream:
    """
    用獨立執行緒讀取攝影機畫面，避免其中一支攝影機的讀取延遲拖累另一支。
    """
    def __init__(self, source, name="Camera"):
        self.source = source
        self.name = name
        self.cap = cv2.VideoCapture(source)

        # 若攝影機支援，可設定解析度（依需求調整或移除）
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.cap.isOpened():
            raise RuntimeError(f"無法開啟攝影機來源: {source}")

        self.frame = None
        self.ret = False
        self.running = True
        self.lock = threading.Lock()

        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            with self.lock:
                self.ret = ret
                self.frame = frame
            if not ret:
                time.sleep(0.01)

    def read(self):
        with self.lock:
            if self.frame is None:
                return False, None
            return self.ret, self.frame.copy()

    def release(self):
        self.running = False
        self.thread.join(timeout=1)
        self.cap.release()


def make_placeholder(width=640, height=480, text="No Signal"):
    """當某支攝影機讀不到畫面時，顯示替代畫面"""
    import numpy as np
    img = np.zeros((height, width, 3), dtype="uint8")
    cv2.putText(img, text, (width // 2 - 100, height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return img


def main():
    # ===== 這裡設定兩支攝影機的來源 =====
    # 若是 USB 攝影機，通常編號為 0, 1, 2 ...
    # 若是 RTSP/IP 攝影機，改成字串網址，例如：
    #   "rtsp://user:password@192.168.1.10:554/stream1"
    source1 = 1
    source2 = 2
    # ====================================

    try:
        cam1 = CameraStream(source1, name="Camera 1")
    except RuntimeError as e:
        print(e)
        return

    try:
        cam2 = CameraStream(source2, name="Camera 2")
    except RuntimeError as e:
        print(e)
        cam1.release()
        return

    print("按下 'q' 鍵結束程式")

    try:
        while True:
            ret1, frame1 = cam1.read()
            ret2, frame2 = cam2.read()

            if not ret1 or frame1 is None:
                frame1 = make_placeholder(text="Camera 1: No Signal")
            if not ret2 or frame2 is None:
                frame2 = make_placeholder(text="Camera 2: No Signal")

            # 統一高度以便並排顯示
            h = min(frame1.shape[0], frame2.shape[0])
            frame1_resized = cv2.resize(frame1, (int(frame1.shape[1] * h / frame1.shape[0]), h))
            frame2_resized = cv2.resize(frame2, (int(frame2.shape[1] * h / frame2.shape[0]), h))

            combined = cv2.hconcat([frame1_resized, frame2_resized])

            cv2.imshow("Dual Camera Stream", combined)

            # 也可以分開顯示，取消下面兩行註解即可
            # cv2.imshow("Camera 1", frame1)
            # cv2.imshow("Camera 2", frame2)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    finally:
        cam1.release()
        cam2.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()