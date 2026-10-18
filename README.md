# Flow

A lightweight, touch-free gesture remote for Android TV and Google TV built with Python, OpenCV, MediaPipe, and the Android TV Remote Protocol v2.

---

## Features

- **Zero Sideloading Required:** Uses the official Google TV Remote Protocol v2 over Wi-Fi with secure on-screen PIN pairing.
- **Natural Swipe Tracking:** Tracks your fingertip motion smoothly across the screen and automatically ignores your hand when moving back to its starting position.
- **Anti-False-Trigger Logic:** Static actions only trigger when your hand is held still, and the remote automatically enters standby after 45 seconds of inactivity.
- **Real-Time HUD:** On-screen visual indicators for fingertip trails, recognized pose, hold progress bar, and sent keycodes.
- **Failover Support:** Automatically attempts native Protocol v2 pairing, with a seamless fallback to ADB over Wi-Fi if needed.

---

## Gestures

| Action | Pose / Movement | Hold / Window | Keycode Sent |
|---|---|---|---|
| **Navigate Left** | Point and swipe left across the screen | < 0.45s | `DPAD_LEFT` |
| **Navigate Right** | Point and swipe right across the screen | < 0.45s | `DPAD_RIGHT` |
| **Navigate Up** | Point and swipe upward across the screen | < 0.45s | `DPAD_UP` |
| **Navigate Down** | Point and swipe downward across the screen | < 0.45s | `DPAD_DOWN` |
| **Safe Move (Clutch)** | Closed fist (0 fingers) | Instant | *Pauses tracking* |
| **Select / Enter** | Pinch (Thumb + Index) **or** Open Palm (5 fingers) held still | Hold 0.45s | `DPAD_CENTER` |
| **Back / Return** | 2 Fingers (Index & middle raised) held still | Hold 0.55s | `BACK` |
| **Volume Up** | 3 Fingers raised and held still | Hold 0.4s (repeats) | `VOLUME_UP` |
| **Volume Down** | 4 Fingers raised (thumb tucked) and held still | Hold 0.4s (repeats) | `VOLUME_DOWN` |
| **Wake from Standby** | Open hand (5 fingers spread) | Hold 1.0s | `WAKE` |

> **Note:** After swiping in any direction, you can naturally move your hand back to the center—Flow automatically ignores the return motion so it won't trigger an accidental opposite swipe.

---

## Installation

### 1. Clone or Download Repository
```bash
git clone [https://github.com/Chirrenthen/flow.git](https://github.com/Chirrenthen/flow.git)
cd flow
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
   - Point and swipe across the screen to navigate menus.
   - Hold a **Pinch** or **Open Hand** still to select, or **2 Fingers** to go back.
   - Close your hand into a **Fist** whenever you want to rest or move your hand without triggering commands.
   - Press `q` or `Esc` inside the camera window to cleanly exit.

---

## Troubleshooting

- **TV not discovered automatically:** Router AP/Client isolation may block multicast traffic. When prompted, enter the TV's IP address manually (find it under *Settings → Network & Internet → [Your Wi-Fi]*).
- **Camera index mismatch:** If you use an external USB webcam, open `config.py` and change `CAMERA_INDEX = 0` to `CAMERA_INDEX = 1`.
- **Reset connection / Pair with a new TV:** Delete `tv_state.json`, `cert.pem`, and `key.pem` from the project folder and re-run `python main.py`.

---

## Attributes
This project contains modified code from: ![kinvi](https://github.com/kinivi/hand-gesture-recognition-mediapipe)

## License
This project is licensed under the ![BSD-3-Clause License](https://github.com/Chirrenthen/flow/blob/main/LICENSE)

Feel free to modify, extend, and use for your maker setups.!
Make sure to leave a star..
