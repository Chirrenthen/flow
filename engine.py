import math
import os
import time
import urllib.request
from collections import deque
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import config

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)
]

OPPOSITE_DIR = {
    "LEFT": "RIGHT",
    "RIGHT": "LEFT",
    "UP": "DOWN",
    "DOWN": "UP",
}

_detector = None
_smoothed = []
_last_ts_ms = 0

_state = {
    "awake": True,
    "last_active": time.monotonic(),
    "trail": deque(maxlen=config.TRAIL_LENGTH),
    "last_swipe_time": 0.0,
    "return_block_dir": None,
    "return_block_until": 0.0,
    "recentered_time": 0.0,
    "pose_name": "NONE",
    "pose_start": 0.0,
    "last_action_time": 0.0,
}


def init_engine():
    global _detector
    if not os.path.exists(config.MODEL_FILE):
        print("Downloading MediaPipe hand model...")
        urllib.request.urlretrieve(config.MODEL_URL, config.MODEL_FILE)
        print("Model ready.")

    base_opts = python.BaseOptions(model_asset_path=config.MODEL_FILE)
    opts = vision.HandLandmarkerOptions(
        base_options=base_opts,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.60,
        min_hand_presence_confidence=0.60,
        min_tracking_confidence=0.60,
    )
    _detector = vision.HandLandmarker.create_from_options(opts)


def _dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def get_quadrant(x, y):
    # Clockwise from Top-Left:
    # Q1: Top-Left  Q2: Top-Right  Q3: Bottom-Right  Q4: Bottom-Left
    if x < 0.5 and y < 0.5:
        return 1
    if x >= 0.5 and y < 0.5:
        return 2
    if x >= 0.5 and y >= 0.5:
        return 3
    return 4


def _classify_hand_pose(lm):
    palm = max(_dist(lm[0], lm[9]), 0.04)
    wrist = lm[0]

    # Check which of the 4 main fingers are extended
    index_up = _dist(lm[8], wrist) > _dist(lm[6], wrist) + 0.10 * palm
    middle_up = _dist(lm[12], wrist) > _dist(lm[10], wrist) + 0.10 * palm
    ring_up = _dist(lm[16], wrist) > _dist(lm[14], wrist) + 0.10 * palm
    pinky_up = _dist(lm[20], wrist) > _dist(lm[18], wrist) + 0.10 * palm
    thumb_up = _dist(lm[4], lm[17]) > _dist(lm[2], lm[17]) + 0.12 * palm

    fingers_count = sum([index_up, middle_up, ring_up, pinky_up])

    # 1. Closed Fist (0 fingers) -> Clutch / Safe Rest
    if fingers_count == 0 and not thumb_up:
        return "CLUTCH"

    # 2. Pinch (Thumb tip touches Index tip) -> Quick Select
    if _dist(lm[4], lm[8]) < 0.30 * palm and fingers_count >= 1:
        return "PINCH"

    # 3. Simple Finger Counts
    if fingers_count == 1 and index_up:
        return "POINT_1"
    if fingers_count == 2 and index_up and middle_up:
        return "PEACE_2"
    if fingers_count == 3 and index_up and middle_up and ring_up:
        return "THREE_3"
    if fingers_count == 4 and not thumb_up:
        return "FOUR_4"
    if fingers_count == 4 and thumb_up:
        return "OPEN_5"

    return "MOVING"


def _is_hand_stationary(now):
    trail = _state["trail"]
    if len(trail) < 4:
        return False
    recent = [pt for pt in trail if now - pt[0] <= 0.20]
    if len(recent) < 3:
        return False
    xs = [pt[1] for pt in recent]
    ys = [pt[2] for pt in recent]
    span = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    return span < config.STILLNESS_MAX_MOVE


def _check_quadrant_swipe(now):
    trail = _state["trail"]
    if len(trail) < 3:
        return None

    _, curr_x, curr_y, curr_q = trail[-1]

    # Expire return guard if time window has passed
    if _state["return_block_dir"] and now >= _state["return_block_until"]:
        _state["return_block_dir"] = None

    for old_t, old_x, old_y, old_q in trail:
        dt = now - old_t
        if dt > config.SWIPE_MAX_TIME or dt < 0.05:
            continue

        dx = curr_x - old_x
        dy = curr_y - old_y
        candidate = None

        # horizontal transitions:
        # left
        if old_q in (2 , 3) and curr_q in (1, 4):
            if dx <= -config.SWIPE_MIN_SPAN and abs(dx) > abs(dy) * 1.25:
                candidate = "LEFT"

        # right
        elif old_q in (1, 4) and curr_q in (2, 3):
            if dx >= config.SWIPE_MIN_SPAN and abs(dx) > abs(dy) * 1.25:
                candidate = "RIGHT"

        # vertical transitions:
        # up
        if candidate is None and old_q in (3, 4) and curr_q in (1, 2):
            if dy <= -config.SWIPE_MIN_SPAN and abs(dy) > abs(dx) * 1.25:
                candidate = "UP"

        # down
        elif candidate is None and old_q in (1, 2) and curr_q in (3, 4):
            if dy >= config.SWIPE_MIN_SPAN and abs(dy) > abs(dx) * 1.25:
                candidate = "DOWN"

        if candidate:
            # check if this is the hand returning to its starting position
            if _state["return_block_dir"] == candidate and now < _state["return_block_until"]:
                _state["return_block_dir"] = None
                _state["return_block_until"] = 0.0
                _state["recentered_time"] = now
                trail.clear()
                return "RECENTERED"

            if now - _state["last_swipe_time"] >= config.SWIPE_COOLDOWN:
                _state["last_swipe_time"] = now
                _state["last_active"] = now
                _state["return_block_dir"] = OPPOSITE_DIR[candidate]
                _state["return_block_until"] = now + config.RETURN_GUARD_TIME
                trail.clear()
                return candidate

    return None


def process_frame(frame):
    global _smoothed, _last_ts_ms
    now = time.monotonic()

    # Auto-standby if completely unused for a long time
    if _state["awake"] and (now - _state["last_active"] > config.IDLE_SLEEP_TIMEOUT):
        _state["awake"] = False
        _state["trail"].clear()

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    now_ms = int(now * 1000)
    if now_ms <= _last_ts_ms:
        now_ms = _last_ts_ms + 1
    _last_ts_ms = now_ms

    result = _detector.detect_for_video(mp_image, now_ms)

    if not result.hand_landmarks:
        _smoothed = []
        _state["trail"].clear()
        _state["pose_name"] = "NONE"
        return None, _build_status(now, None, 0.0)

    raw = [(lm.x, lm.y) for lm in result.hand_landmarks[0]]
    alpha = config.SMOOTHING_FACTOR
    if not _smoothed:
        _smoothed = raw
    else:
        _smoothed = [
            (alpha * rx + (1 - alpha) * sx, alpha * ry + (1 - alpha) * sy)
            for (rx, ry), (sx, sy) in zip(raw, _smoothed)
        ]

    pose = _classify_hand_pose(_smoothed)

    # Track Index Fingertip (landmark 8) for Quadrant & Point History
    tip_x, tip_y = _smoothed[8]
    curr_q = get_quadrant(tip_x, tip_y)

    # If in CLUTCH (Closed Fist), pause tracking so hand can move freely
    if pose == "CLUTCH":
        _state["trail"].clear()
        _state["return_block_dir"] = None
        _state["pose_name"] = "CLUTCH (Safe Move)"
        return None, _build_status(now, _smoothed, 0.0, curr_q)

    _state["trail"].append((now, tip_x, tip_y, curr_q))

    # If asleep, wake up on Open Palm
    if not _state["awake"]:
        if pose == "OPEN_5":
            if _state["pose_name"] != "OPEN_5":
                _state["pose_name"] = "OPEN_5"
                _state["pose_start"] = now
            held = now - _state["pose_start"]
            prog = min(held / config.WAKE_HOLD_TIME, 1.0)
            if held >= config.WAKE_HOLD_TIME:
                _state["awake"] = True
                _state["last_active"] = now
                _state["trail"].clear()
                return "WAKE", _build_status(now, _smoothed, 1.0, curr_q)
            return None, _build_status(now, _smoothed, prog, curr_q)
        _state["pose_name"] = pose
        return None, _build_status(now, _smoothed, 0.0, curr_q)

    # check for swipe
    swipe_res = _check_quadrant_swipe(now)
    if swipe_res == "RECENTERED":
        _state["pose_name"] = "RETURN IGNORED"
        return None, _build_status(now, _smoothed, 0.0, curr_q)
    if swipe_res:
        _state["pose_name"] = f"SWIPE {swipe_res}"
        return swipe_res, _build_status(now, _smoothed, 0.0, curr_q)

    # check still hand
    stationary = _is_hand_stationary(now)
    if not stationary or pose in ("POINT_1", "MOVING"):
        _state["pose_name"] = pose
        _state["pose_start"] = now
        return None, _build_status(now, _smoothed, 0.0, curr_q)

    if pose != _state["pose_name"]:
        _state["pose_name"] = pose
        _state["pose_start"] = now

    held_time = now - _state["pose_start"]

    action_map = {
        "PINCH": ("SELECT", config.SELECT_HOLD_TIME, config.ACTION_COOLDOWN),
        "OPEN_5": ("SELECT", config.SELECT_HOLD_TIME, config.ACTION_COOLDOWN),
        "PEACE_2": ("BACK", config.BACK_HOLD_TIME, config.ACTION_COOLDOWN),
        "THREE_3": ("VOL_UP", config.VOLUME_HOLD_TIME, config.VOLUME_REPEAT_INTERVAL),
        "FOUR_4": ("VOL_DOWN", config.VOLUME_HOLD_TIME, config.VOLUME_REPEAT_INTERVAL),
    }

    if pose in action_map:
        cmd, req_hold, cooldown = action_map[pose]
        progress = min(held_time / req_hold, 1.0)
        if held_time >= req_hold and (now - _state["last_action_time"] >= cooldown):
            _state["last_action_time"] = now
            _state["last_active"] = now
            if cmd in ("SELECT", "BACK"):
                _state["pose_start"] = now + 0.5
            return cmd, _build_status(now, _smoothed, 1.0, curr_q)
        return None, _build_status(now, _smoothed, progress, curr_q)

    return None, _build_status(now, _smoothed, 0.0, curr_q)


def _build_status(now, landmarks, progress, quadrant=None):
    guard_rem = max(0.0, _state["return_block_until"] - now) if _state["return_block_dir"] else 0.0
    return {
        "awake": _state["awake"],
        "pose": _state["pose_name"],
        "progress": progress,
        "quadrant": quadrant,
        "landmarks": landmarks,
        "trail": list(_state["trail"]),
        "return_guard": _state["return_block_dir"] if guard_rem > 0 else None,
        "recentered_flash": (now - _state["recentered_time"]) < 0.65,
    }
