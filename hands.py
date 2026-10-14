import os
import time
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import config

_detector = None
_smoothed = []
_last_timestamp_ms = 0

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)
]


def init_hands():
    global _detector
    if not os.path.exists(config.MODEL_FILE):
        print("Downloading MediaPipe hand model (one-time 7.5MB download)...")
        urllib.request.urlretrieve(config.MODEL_URL, config.MODEL_FILE)
        print("Model ready.")

    base_options = python.BaseOptions(model_asset_path=config.MODEL_FILE)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.65,
        min_hand_presence_confidence=0.65,
        min_tracking_confidence=0.65,
    )
    _detector = vision.HandLandmarker.create_from_options(options)


def get_landmarks(frame):
    global _smoothed, _last_timestamp_ms
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    now_ms = int(time.monotonic() * 1000)
    if now_ms <= _last_timestamp_ms:
        now_ms = _last_timestamp_ms + 1
    _last_timestamp_ms = now_ms

    result = _detector.detect_for_video(mp_image, now_ms)
    if not result.hand_landmarks:
        _smoothed = []
        return None

    raw = [(lm.x, lm.y) for lm in result.hand_landmarks[0]]
    alpha = config.SMOOTHING_FACTOR

    if not _smoothed:
        _smoothed = raw
    else:
        _smoothed = [
            (alpha * rx + (1 - alpha) * sx, alpha * ry + (1 - alpha) * sy)
            for (rx, ry), (sx, sy) in zip(raw, _smoothed)
        ]

    return _smoothed


def draw_hand(frame, landmarks):
    if not landmarks:
        return
    h, w, _ = frame.shape
    pts = [(int(x * w), int(y * h)) for x, y in landmarks]

    for a, b in CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 220, 120), 2)
    for pt in pts:
        cv2.circle(frame, pt, 4, (255, 255, 255), -1)