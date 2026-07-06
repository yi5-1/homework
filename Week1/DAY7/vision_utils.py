import cv2
import numpy as np
import os


def ensure_odd(value: int) -> int:
    """確保數值為奇數，適用於 GaussianBlur kernel size。"""
    value = max(1, int(value))
    return value if value % 2 == 1 else value + 1


def load_face_cascade(cascade_path: str):
    """載入人臉 Haarcascade。如果失敗，嘗試使用 OpenCV 內建路徑。"""
    cascade_cls = getattr(cv2, "CascadeClassifier", None)
    if cascade_cls is None:
        cv2_inner = getattr(cv2, "cv2", None)
        cascade_cls = getattr(cv2_inner, "CascadeClassifier", None) if cv2_inner is not None else None

    if cascade_cls is None:
        return None

    if os.path.exists(cascade_path):
        cc = cascade_cls(cascade_path)
        if not cc.empty():
            return cc

    try:
        alt_path = None
        if hasattr(cv2, "data"):
            alt_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if alt_path is None or not os.path.exists(alt_path):
            opencv_data = os.path.join(os.path.dirname(cv2.__file__), "data")
            alt_path = os.path.join(opencv_data, "haarcascade_frontalface_default.xml")
        if os.path.exists(alt_path):
            cc = cascade_cls(alt_path)
            if not cc.empty():
                return cc
    except Exception:
        pass

    return None


def enumerate_cameras(max_devices: int = 10) -> list[int]:
    """掃描可用相機索引。"""
    cameras = []
    for i in range(max_devices):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            cameras.append(i)
            cap.release()
    return cameras


def preprocess_frame(frame, ksize: int, sigma: float, t1: int, t2: int):
    """進行灰階、Blur、Canny 前處理。"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ksize = ensure_odd(ksize)
    blur = cv2.GaussianBlur(gray, (ksize, ksize), sigma)
    edges = cv2.Canny(blur, t1, t2)
    return gray, blur, edges


def draw_shape_annotations(out, edges, min_area: int, max_area: int,
                           eps_pct: int, circ_thr: int,
                           show_tri: bool, show_sq: bool,
                           show_ci: bool, show_pg: bool):
    """根據 Canny 邊緣結果繪製形狀偵測標記。"""
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    counts = {"Triangle": 0, "Square": 0, "Rectangle": 0, "Circle": 0, "Polygon": 0}

    eps_ratio = max(eps_pct, 1) / 100.0
    circularity_threshold = circ_thr / 100.0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        perimeter = cv2.arcLength(cnt, True)
        if perimeter <= 0:
            continue

        hull = cv2.convexHull(cnt)
        approx = cv2.approxPolyDP(hull, eps_ratio * cv2.arcLength(hull, True), True)
        vtx = len(approx)
        circularity = 4 * np.pi * area / (perimeter * perimeter)

        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])

        shape, color = None, (255, 255, 255)
        if show_ci and circularity > circularity_threshold and vtx >= 5:
            shape = "Circle"
            color = (0, 0, 255)
            counts["Circle"] += 1
        elif show_tri and vtx == 3:
            shape = "Triangle"
            color = (0, 255, 255)
            counts["Triangle"] += 1
        elif show_sq and vtx == 4:
            x, y, w, h = cv2.boundingRect(approx)
            ratio = w / float(h) if h > 0 else 0
            if 0.85 <= ratio <= 1.15:
                shape = "Square"
                counts["Square"] += 1
            else:
                shape = "Rectangle"
                counts["Rectangle"] += 1
            color = (0, 255, 0)
        elif show_pg and vtx >= 5:
            shape = f"Polygon-{vtx}"
            color = (255, 100, 200)
            counts["Polygon"] += 1

        if shape:
            cv2.drawContours(out, [approx], -1, color, 2)
            cv2.circle(out, (cX, cY), 4, color, -1)
            cv2.putText(out, f"{shape} A:{int(area)}",
                        (cX - 55, cY - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    return out, counts


def draw_face_detections(out, gray, face_cascade, scale_factor: float,
                         min_neighbors: int, min_size: int, eye_mask: int):
    """使用 Haarcascade 偵測人臉並繪製標記。"""
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=scale_factor,
        minNeighbors=min_neighbors,
        minSize=(min_size, min_size),
    )

    for (x, y, w, h) in faces:
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(out, f"Face {w}x{h}", (x, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if eye_mask:
            ey1 = y + int(h * 0.25)
            ey2 = y + int(h * 0.55)
            ex_l = x + int(w * 0.05)
            ex_r = x + int(w * 0.95)
            if eye_mask == 1:
                cv2.rectangle(out, (ex_l, ey1), (ex_r, ey2), (0, 0, 0), -1)
            elif eye_mask == 2:
                ew = ex_r - ex_l
                eh = ey2 - ey1
                if ew > 0 and eh > 0:
                    roi = out[ey1:ey2, ex_l:ex_r]
                    small = cv2.resize(roi, (max(ew // 12, 1), max(eh // 8, 1)),
                                       interpolation=cv2.INTER_LINEAR)
                    roi[:] = cv2.resize(small, (ew, eh), interpolation=cv2.INTER_NEAREST)

    return out, len(faces)
