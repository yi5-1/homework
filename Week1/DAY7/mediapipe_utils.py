import cv2
import mediapipe as mp
from mediapipe.tasks import python


def create_face_landmarker(model_path: str, num_faces: int = 3):
    """建立 FaceLandmarker 模型並回傳模型物件與 mp.tasks.vision 模組。"""
    mp_vision = mp.tasks.vision
    options = mp_vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=model_path),
        running_mode=mp_vision.RunningMode.VIDEO,
        num_faces=num_faces,
        output_face_blendshapes=False,
    )
    face_landmarker = mp_vision.FaceLandmarker.create_from_options(options)
    return face_landmarker, mp_vision


def frame_to_mp_image(frame):
    """將 OpenCV BGR 影像轉換為 MediaPipe 可處理的 mp.Image。"""
    return mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
    )


def detect_face_landmarks(frame, face_landmarker, mp_vision, timestamp: int):
    """使用 FaceLandmarker 對影片幀執行偵測。"""
    mp_image = frame_to_mp_image(frame)
    return face_landmarker.detect_for_video(mp_image, timestamp)


def draw_face_mesh(out, results, mp_vision):
    """將偵測結果繪製成 Face Mesh。"""
    du = mp_vision.drawing_utils
    ds = mp_vision.drawing_styles
    fc = mp_vision.FaceLandmarksConnections
    num_faces = 0

    if results.face_landmarks:
        h, w = out.shape[:2]
        for face_landmarks in results.face_landmarks:
            num_faces += 1
            du.draw_landmarks(
                image=out,
                landmark_list=face_landmarks,
                connections=fc.FACE_LANDMARKS_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=ds.get_default_face_mesh_tesselation_style(),
            )
            du.draw_landmarks(
                image=out,
                landmark_list=face_landmarks,
                connections=fc.FACE_LANDMARKS_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=ds.get_default_face_mesh_contours_style(),
            )
            du.draw_landmarks(
                image=out,
                landmark_list=face_landmarks,
                connections=fc.FACE_LANDMARKS_LEFT_IRIS,
                landmark_drawing_spec=None,
                connection_drawing_spec=ds.get_default_face_mesh_iris_connections_style(),
            )
            du.draw_landmarks(
                image=out,
                landmark_list=face_landmarks,
                connections=fc.FACE_LANDMARKS_RIGHT_IRIS,
                landmark_drawing_spec=None,
                connection_drawing_spec=ds.get_default_face_mesh_iris_connections_style(),
            )
            for lm in face_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(out, (cx, cy), 1, (0, 255, 255), -1)

    return out, num_faces
