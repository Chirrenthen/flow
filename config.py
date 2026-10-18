import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


STATE_FILE = os.path.join(BASE_DIR, "tv_state.json")
CERT_FILE = os.path.join(BASE_DIR, "cert.pem")
KEY_FILE = os.path.join(BASE_DIR, "key.pem")
MODEL_FILE = os.path.join(BASE_DIR, "hand_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)

# Camera settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Point history & smoothing
TRAIL_LENGTH = 16             # Number of fingertip points stored in trail
SMOOTHING_FACTOR = 0.50       # EMA smoothing (0.5 balances speed and stability)

# Quadrant Swipe settings
SWIPE_MIN_SPAN = 0.18         # Must travel at least 18% of screen across quadrant line
SWIPE_MAX_TIME = 0.45         # Max seconds for a deliberate swipe crossing
SWIPE_COOLDOWN = 0.35         # Minimum time between two consecutive swipes
RETURN_GUARD_TIME = 1.50      # Seconds to absorb opposite-direction return movement

# Stationary Action Hold Times (only count when hand is still)
STILLNESS_MAX_MOVE = 0.045    # Max hand movement allowed to be considered "stationary"
SELECT_HOLD_TIME = 0.45       # Pinch or Open Palm (5 fingers) held still -> SELECT
BACK_HOLD_TIME = 0.55         # 2 Fingers (Peace) held still -> BACK
VOLUME_HOLD_TIME = 0.40       # 3 Fingers (Vol+) or 4 Fingers (Vol-) held still
ACTION_COOLDOWN = 0.75        # Cooldown after Select / Back
VOLUME_REPEAT_INTERVAL = 0.35 # Repeat interval while holding Volume pose

# Idle auto-sleep (seconds of zero activity before standby; wakes on 1s Open Palm)
IDLE_SLEEP_TIMEOUT = 45.0
WAKE_HOLD_TIME = 1.0
