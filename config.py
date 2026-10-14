import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Auto-generated files
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

# Smoothing and failsafe timeouts (seconds)
SMOOTHING_FACTOR = 0.45       # Lower = smoother, Higher = faster response
IDLE_LOCK_TIMEOUT = 8.0       # Lock system after 8s of no actions

# Hold durations required to trigger static gestures (seconds)
WAKE_HOLD_TIME = 1.5          # Open palm to unlock/lock
PINCH_HOLD_TIME = 0.35        # Thumb + Index pinch for OK/Select
BACK_HOLD_TIME = 0.60         # Peace sign for Back
VOLUME_HOLD_TIME = 0.40       # Point up / Fist for Volume
POWER_HOLD_TIME = 2.50        # Rock-on sign for Power Off

# Cooldowns between actions (seconds)
SWIPE_COOLDOWN = 0.50
ACTION_COOLDOWN = 0.80
VOLUME_REPEAT_INTERVAL = 0.35

# Normalized movement thresholds (relative to palm size)
SWIPE_MIN_DISTANCE = 0.65     # Must move 65% of palm size within window
SWIPE_TIME_WINDOW = 0.22      # Seconds to complete a swipe
PINCH_THRESHOLD = 0.32        # Thumb-to-index distance ratio vs palm size