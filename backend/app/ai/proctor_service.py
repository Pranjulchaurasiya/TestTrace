"""Computer Vision and biometric proctoring analysis service for TestTrace."""

import io
import json
import os
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import mediapipe as mp
except ImportError:
    mp = None

# Lazy-loaded YOLO model for phone/device detection
_yolo_model = None

def get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        try:
            from ultralytics import YOLO
            # Lightweight nano weights (approx 6MB)
            _yolo_model = YOLO("yolov8n.pt")
        except Exception as e:
            print(f"[ProctorService] YOLO initialization notice: {e}")
            _yolo_model = False
    return _yolo_model if _yolo_model is not False else None


def detect_phone_in_frame(frame: np.ndarray) -> tuple[bool, float]:
    """Runs lightweight object detection to detect mobile phones (COCO class 67)."""
    model = get_yolo_model()
    if not model or frame is None:
        return False, 0.0

    try:
        # Run inference on cell phone (class 67)
        results = model.predict(source=frame, classes=[67], conf=0.45, verbose=False)
        for r in results:
            if len(r.boxes) > 0:
                conf = float(r.boxes.conf[0].item())
                return True, round(conf, 2)
    except Exception as e:
        print(f"[ProctorService] Phone detection error: {e}")

    return False, 0.0


def calculate_risk_level(suspicious_score: int) -> str:
    """Standardized risk level evaluation."""
    if suspicious_score >= 100:
        return "CRITICAL"
    elif suspicious_score >= 80:
        return "HIGH"
    elif suspicious_score >= 50:
        return "MEDIUM"
    elif suspicious_score >= 30:
        return "WARNING"
    return "LOW"


# Cached Haar cascade classifier for accurate face detection
_face_cascade = None

def get_face_cascade():
    global _face_cascade
    if _face_cascade is None and cv2:
        alt2_path = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
        default_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if os.path.exists(alt2_path):
            _face_cascade = cv2.CascadeClassifier(alt2_path)
        elif os.path.exists(default_path):
            _face_cascade = cv2.CascadeClassifier(default_path)
    return _face_cascade


def decode_image_bytes(image_bytes: bytes) -> np.ndarray | None:
    """Decodes raw binary image bytes into a BGR OpenCV numpy array."""
    if not cv2:
        return None
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def analyze_frame_telemetry(image_bytes: bytes) -> dict:
    """Analyzes a student frame for faces, head orientation, and gaze direction."""
    frame = decode_image_bytes(image_bytes)

    if frame is None or not cv2:
        return {
            "faces_detected": 0,
            "gaze_status": "LOOKING_AWAY",
            "head_pose_direction": "UNKNOWN",
            "phone_detected": False,
            "violation": None,
            "points": 0,
        }

    h, w, _ = frame.shape
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    # Face detection using tuned Haar cascade
    face_cascade = get_face_cascade()
    faces = []
    if face_cascade and not face_cascade.empty():
        raw_faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=6,
            minSize=(50, 50),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        # Filter for plausible human face aspect ratio (height-to-width ratio ~ 0.75 - 1.35)
        for (fx, fy, fw, fh) in raw_faces:
            aspect = fh / float(fw)
            if 0.75 <= aspect <= 1.35:
                faces.append((fx, fy, fw, fh))

    face_count = len(faces)

    if face_count == 0:
        return {
            "faces_detected": 0,
            "gaze_status": "LOOKING_AWAY",
            "head_pose_direction": "UNKNOWN",
            "phone_detected": False,
            "violation": "FACE_MISSING",
            "points": 1,
            "metadata": {"reason": "No face detected in camera viewport"},
        }
    elif face_count > 1:
        return {
            "faces_detected": face_count,
            "gaze_status": "NORMAL",
            "head_pose_direction": "NORMAL",
            "phone_detected": False,
            "violation": "MULTIPLE_FACES",
            "points": 5,
            "metadata": {"face_count": face_count},
        }

    # Evaluate head orientation based on primary face bounding box offset
    (x, y, fw, fh) = faces[0]
    face_center_x = x + fw / 2.0
    frame_center_x = w / 2.0
    offset_ratio = (face_center_x - frame_center_x) / (w / 2.0)

    head_direction = "STRAIGHT"
    violation = None
    points = 0

    if offset_ratio > 0.40:
        head_direction = "RIGHT"
        violation = "LOOKING_RIGHT"
        points = 2
    elif offset_ratio < -0.40:
        head_direction = "LEFT"
        violation = "LOOKING_LEFT"
        points = 2

    # Check for unauthorized phone presence
    phone_found, phone_conf = detect_phone_in_frame(frame)

    if phone_found:
        violation = "PHONE_DETECTED"
        points = 10

    return {
        "faces_detected": 1,
        "gaze_status": "FOCUSED" if (violation is None) else "LOOKING_AWAY",
        "head_pose_direction": head_direction,
        "phone_detected": phone_found,
        "violation": violation,
        "points": points,
        "metadata": {
            "offset_ratio": round(float(offset_ratio), 3),
            "face_box": [int(x), int(y), int(fw), int(fh)],
            "phone_confidence": phone_conf if phone_found else None,
        },
    }
