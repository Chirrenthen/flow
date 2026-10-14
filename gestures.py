import math
import time
from collections import deque
import config

_state = {
    "awake": False,
    "last_active": 0.0,
    "last_trigger": 0.0,
    "pose_name": None,
    "pose_start": 0.0,
    "history": deque(maxlen=12),
}


def _dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _palm_size(lm):
    return max(_dist(lm[0], lm[9]), 0.04)


def _detect_static_pose(lm):
    palm = _palm_size(lm)
    wrist = lm[0]

    # A finger is extended if its tip is noticeably further from wrist than its PIP joint
    index_up = _dist(lm[8], wrist) > _dist(lm[6], wrist) + 0.12 * palm
    middle_up = _dist(lm[12], wrist) > _dist(lm[10], wrist) + 0.12 * palm
    ring_up = _dist(lm[16], wrist) > _dist(lm[14], wrist) + 0.12 * palm
    pinky_up = _dist(lm[20], wrist) > _dist(lm[18], wrist) + 0.12 * palm

    # Thumb is open if its tip is far from the pinky knuckle
    thumb_open = _dist(lm[4], lm[17]) > 0.85 * palm

    # Pinch: thumb and index tips close together, middle & ring stay up to avoid fist confusion
    if _dist(lm[4], lm[8]) < config.PINCH_THRESHOLD * palm and middle_up and ring_up:
        return "PINCH"

    if index_up and middle_up and ring_up and pinky_up and thumb_open:
        return "OPEN_PALM"

    if index_up and pinky_up and not middle_up and not ring_up:
        return "ROCK_ON"

    if index_up and middle_up and not ring_up and not pinky_up:
        return "PEACE"

    if index_up and not middle_up and not ring_up and not pinky_up:
        return "POINT_UP"

    if not index_up and not middle_up and not ring_up and not pinky_up and not thumb_open:
        return "FIST"

    return "NEUTRAL"


def _detect_swipe(now, palm):
    hist = _state["history"]
    if len(hist) < 3:
        return None

    for old_t, old_x, old_y in hist:
        dt = now - old_t
        if 0.06 <= dt <= config.SWIPE_TIME_WINDOW:
            dx = (hist[-1][1] - old_x) / palm
            dy = (hist[-1][2] - old_y) / palm

            if abs(dx) > config.SWIPE_MIN_DISTANCE and abs(dx) > abs(dy) * 1.6:
                hist.clear()
                return "RIGHT" if dx > 0 else "LEFT"

            if abs(dy) > config.SWIPE_MIN_DISTANCE and abs(dy) > abs(dx) * 1.6:
                hist.clear()
                return "DOWN" if dy > 0 else "UP"
    return None


def update_gesture(landmarks):
    now = time.monotonic()

    # Auto-lock on idle timeout
    if _state["awake"] and (now - _state["last_active"] > config.IDLE_LOCK_TIMEOUT):
        _state["awake"] = False
        _state["pose_name"] = None
        _state["history"].clear()

    if landmarks is None:
        _state["pose_name"] = None
        _state["history"].clear()
        return None, _get_ui_status(now, 0.0)

    palm = _palm_size(landmarks)
    _state["history"].append((now, landmarks[0][0], landmarks[0][1]))
    pose = _detect_static_pose(landmarks)

    if pose != _state["pose_name"]:
        _state["pose_name"] = pose
        _state["pose_start"] = now

    held_time = now - _state["pose_start"]

    # 1. Handle Wake / Sleep toggle (Open Palm)
    if pose == "OPEN_PALM":
        progress = min(held_time / config.WAKE_HOLD_TIME, 1.0)
        if held_time >= config.WAKE_HOLD_TIME and (now - _state["last_trigger"] > 1.2):
            _state["awake"] = not _state["awake"]
            _state["last_active"] = now
            _state["last_trigger"] = now
            _state["pose_start"] = now + 2.0
            return ("WAKE" if _state["awake"] else "SLEEP"), _get_ui_status(now, 1.0)
        return None, _get_ui_status(now, progress)

    # Ignore all other commands while locked
    if not _state["awake"]:
        return None, _get_ui_status(now, 0.0)

    # 2. Check Swipes first (only if not holding a deliberate command pose)
    if pose in ("NEUTRAL", "OPEN_PALM") and (now - _state["last_trigger"] > config.SWIPE_COOLDOWN):
        swipe = _detect_swipe(now, palm)
        if swipe:
            _state["last_active"] = now
            _state["last_trigger"] = now
            return swipe, _get_ui_status(now, 0.0)

    # 3. Check Held Static Gestures
    hold_map = {
        "PINCH": ("SELECT", config.PINCH_HOLD_TIME, config.ACTION_COOLDOWN),
        "PEACE": ("BACK", config.BACK_HOLD_TIME, config.ACTION_COOLDOWN),
        "POINT_UP": ("VOL_UP", config.VOLUME_HOLD_TIME, config.VOLUME_REPEAT_INTERVAL),
        "FIST": ("VOL_DOWN", config.VOLUME_HOLD_TIME, config.VOLUME_REPEAT_INTERVAL),
        "ROCK_ON": ("POWER", config.POWER_HOLD_TIME, 3.0),
    }

    if pose in hold_map:
        cmd, req_hold, cooldown = hold_map[pose]
        progress = min(held_time / req_hold, 1.0)
        if held_time >= req_hold and (now - _state["last_trigger"] >= cooldown):
            _state["last_active"] = now
            _state["last_trigger"] = now
            if cmd == "POWER":
                _state["awake"] = False
            return cmd, _get_ui_status(now, 1.0)
        return None, _get_ui_status(now, progress)

    return None, _get_ui_status(now, 0.0)


def _get_ui_status(now, progress):
    rem = max(0.0, config.IDLE_LOCK_TIMEOUT - (now - _state["last_active"])) if _state["awake"] else 0.0
    return {
        "awake": _state["awake"],
        "pose": _state["pose_name"] or "NONE",
        "progress": progress,
        "timeout_in": rem,
    }