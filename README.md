# Flow

A lightweight, touch-free gesture remote for Android TV and Google TV built with Python, OpenCV, MediaPipe, and the Android TV Remote Protocol v2.

---

## Features

- **Zero Sideloading Required:** Uses the official Google TV Remote Protocol v2 over Wi-Fi with secure on-screen PIN pairing.
- **Palm-Relative Calibration:** All motion vectors and finger spreads are normalized against palm size, making tracking distance- and hand-size agnostic.
- **Fatigue-Free Ergonomics:** Designed for micro-swipes and relaxed postures—rest your elbow on your armrest and flick your wrist.
- **Anti-False-Trigger Logic:** Auto-locks after 8 seconds of inactivity and requires a deliberate 1.5-second open-palm hold to activate.
- **Real-Time HUD:** On-screen visual indicators for connection status, recognized pose, hold progress bar, and sent keycodes.
- **Failover Support:** Automatically attempts native Protocol v2 pairing, with a seamless fallback to ADB over Wi-Fi if needed.

---

## Gesture Cheat Sheet

| Action | Pose / Movement | Hold / Window | Keycode Sent |
|---|---|---|---|
| **Wake / Sleep Toggle** | Open hand, 5 fingers spread (`OPEN_PALM`) | Hold 1.5s | `WAKE` / `SLEEP` |
| **Navigate Left** | Quick horizontal flick to the left | < 0.22s | `DPAD_LEFT` |
| **Navigate Right** | Quick horizontal flick to the right | < 0.22s | `DPAD_RIGHT` |
| **Navigate Up** | Quick vertical flick upward | < 0.22s | `DPAD_UP` |
| **Navigate Down** | Quick vertical flick downward | < 0.22s | `DPAD_DOWN` |
| **Select / Enter** | Thumb tip touches index tip (`PINCH`) | Hold 0.35s | `DPAD_CENTER` |
| **Back / Return** | Index & middle fingers raised (`PEACE`) | Hold 0.6s | `BACK` |
| **Volume Up** | Index finger pointing up (`POINT_UP`) | Hold 0.4s (repeats) | `VOLUME_UP` |
| **Volume Down** | Closed fist (`FIST`) | Hold 0.4s (repeats) | `VOLUME_DOWN` |
| **Power Toggle** | Index & pinky extended (`ROCK_ON`) | Hold 2.5s | `POWER` |

> **Note:** The system defaults to **LOCKED** on startup. Hold an **Open Palm** for 1.5 seconds until the status bar turns green before issuing commands.

## Installation

### 1. Clone or Download Repository
```bash
git clone [https://github.com/your-username/wavetv.git](https://github.com/your-username/wavetv.git)
cd wavetv
```

### 2. Set Up a Virtual Environment

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.bat
```

### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

*(On first run, the script will automatically fetch Google's 7.5 MB `hand_landmarker.task` model file).*

---

## First-Run Setup & Pairing

1. Turn on your Android TV.
2. Launch the application:
   ```bash
   python main.py
   ```
3. **Auto-Discovery & Pairing:**
   - The script will scan your network using mDNS for 3 seconds.
   - Once your TV is found, your TV screen will display an on-screen **6-digit pairing PIN**.
   - Enter the 6-digit PIN in your terminal and hit `Enter`.
   - Local SSL certificates (`cert.pem`, `key.pem`) and your TV state (`tv_state.json`) will be cached locally. Subsequent runs connect automatically.
4. **Operation:**
   - Hold an **Open Palm** steady for 1.5 seconds to unlock.
   - Use swipes for navigation and pinch to select.
   - Press `q` or `Esc` inside the camera window to cleanly exit.

---

## Troubleshooting

- **TV not discovered automatically:** Router AP/Client isolation may block multicast traffic. When prompted, enter the TV's IP address manually (find it under *Settings → Network & Internet → [Your Wi-Fi]*).
- **Camera index mismatch:** If you use an external USB webcam, open `config.py` and change `CAMERA_INDEX = 0` to `CAMERA_INDEX = 1`.
- **Reset connection / Pair with a new TV:** Delete `tv_state.json`, `cert.pem`, and `key.pem` from the project folder and re-run `python main.py`.

---

Feel free to modify, extend, and use for your maker setups.!
Make sure to leave a star..