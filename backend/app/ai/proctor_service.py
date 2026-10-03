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


# In-memory enrolled face signatures and frame counters per exam attempt
_enrolled_face_signatures: dict[int, np.ndarray] = {}
_frame_counters: dict[int, int] = {}


def extract_face_signature(face_bgr: np.ndarray) -> np.ndarray:
    """Extracts normalized spatial & color signature for continuous identity verification."""
    face_norm = cv2.resize(face_bgr, (120, 120))
    # 1. Spatial grayscale histogram (4x4 grid of 30x30 blocks)
    gray = cv2.cvtColor(face_norm, cv2.COLOR_BGR2GRAY)
    blocks_gray = [gray[r:r+30, c:c+30] for r in range(0, 120, 30) for c in range(0, 120, 30)]
    hists_gray = [cv2.normalize(cv2.calcHist([b], [0], None, [16], [0, 256]), None).flatten() for b in blocks_gray]

    # 2. HSV color distribution (Hue & Saturation)
    hsv = cv2.cvtColor(face_norm, cv2.COLOR_BGR2HSV)
    blocks_hsv = [hsv[r:r+40, c:c+40] for r in range(0, 120, 40) for c in range(0, 120, 40)]
    hists_hsv = [cv2.normalize(cv2.calcHist([b], [0, 1], None, [8, 8], [0, 180, 0, 256]), None).flatten() for b in blocks_hsv]

    sig = np.concatenate(hists_gray + hists_hsv).astype(np.float32)
    return sig


def compare_face_signatures(sig1: np.ndarray, sig2: np.ndarray) -> float:
    """Compares two facial signatures using histogram correlation (-1.0 to 1.0)."""
    if sig1 is None or sig2 is None:
        return 0.0
    return float(cv2.compareHist(sig1, sig2, cv2.HISTCMP_CORREL))


def analyze_frame_telemetry(image_bytes: bytes, attempt_id: int | None = None) -> dict:
    """Analyzes a student frame for faces, identity match, head orientation, and gaze direction."""
    frame = decode_image_bytes(image_bytes)

    if frame is None or not cv2:
        return {
            "faces_detected": 0,
            "identity_verified": False,
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
            "identity_verified": False,
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
            "identity_verified": False,
            "gaze_status": "NORMAL",
            "head_pose_direction": "NORMAL",
            "phone_detected": False,
            "violation": "MULTIPLE_FACES",
            "points": 5,
            "metadata": {"face_count": face_count},
        }

    # Evaluate primary face ROI and biometric identity matching against enrolled student
    (x, y, fw, fh) = faces[0]
    face_roi = frame[max(0, y):min(h, y+fh), max(0, x):min(w, x+fw)]
    identity_verified = True
    similarity_score = 1.0

    if attempt_id is not None and face_roi.size > 0:
        current_sig = extract_face_signature(face_roi)
        if attempt_id not in _enrolled_face_signatures:
            # First clean face detected in session: Enroll as student baseline identity signature
            _enrolled_face_signatures[attempt_id] = current_sig
            identity_verified = True
            similarity_score = 1.0
        else:
            enrolled_sig = _enrolled_face_signatures[attempt_id]
            similarity_score = compare_face_signatures(enrolled_sig, current_sig)
            if similarity_score >= 0.40:
                identity_verified = True
                # Smooth adaptive update to accommodate subtle lighting/head angle variations
                _enrolled_face_signatures[attempt_id] = (0.90 * enrolled_sig + 0.10 * current_sig).astype(np.float32)
            else:
                identity_verified = False

    face_center_x = x + fw / 2.0
    frame_center_x = w / 2.0
    offset_ratio = (face_center_x - frame_center_x) / (w / 2.0)

    head_direction = "STRAIGHT"
    violation = None
    points = 0

    if not identity_verified:
        violation = "FACE_MISMATCH"
        points = 8
    elif offset_ratio > 0.40:
        head_direction = "RIGHT"
        violation = "LOOKING_RIGHT"
        points = 2
    elif offset_ratio < -0.40:
        head_direction = "LEFT"
        violation = "LOOKING_LEFT"
        points = 2

    # Check for unauthorized phone presence periodically (every 6th frame to maintain 20ms response time)
    phone_found = False
    phone_conf = 0.0
    if attempt_id is not None:
        cnt = _frame_counters.get(attempt_id, 0) + 1
        _frame_counters[attempt_id] = cnt
        if cnt % 6 == 1:
            phone_found, phone_conf = detect_phone_in_frame(frame)

    if phone_found:
        violation = "PHONE_DETECTED"
        points = 10

    return {
        "faces_detected": 1,
        "identity_verified": identity_verified,
        "identity_similarity": round(float(similarity_score), 3),
        "gaze_status": "FOCUSED" if (violation is None) else "LOOKING_AWAY",
        "head_pose_direction": head_direction,
        "phone_detected": phone_found,
        "violation": violation,
        "points": points,
        "metadata": {
            "offset_ratio": round(float(offset_ratio), 3),
            "similarity_score": round(float(similarity_score), 3),
            "face_box": [int(x), int(y), int(fw), int(fh)],
            "phone_confidence": phone_conf if phone_found else None,
        },
    }
