import time
import cv2
import camera
import hands
import gestures
import tv


def draw_hud(frame, status, last_cmd, last_cmd_time):
    h, w, _ = frame.shape
    awake = status["awake"]

    # Top banner
    banner_color = (20, 140, 20) if awake else (40, 40, 160)
    cv2.rectangle(frame, (0, 0), (w, 52), banner_color, -1)

    state_txt = f"ACTIVE (Locks in {status['timeout_in']:.1f}s)" if awake else "LOCKED (Hold Open Palm 1.5s)"
    cv2.putText(frame, state_txt, (15, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Pose indicator
    cv2.putText(frame, f"Pose: {status['pose']}", (w - 210, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1)

    # Hold progress bar
    if status["progress"] > 0.05:
        bar_w = int(w * status["progress"])
        cv2.rectangle(frame, (0, 52), (bar_w, 62), (0, 255, 255), -1)

    # Recent triggered command flash
    if last_cmd and (time.monotonic() - last_cmd_time < 1.0):
        cv2.putText(frame, f"SENT: {last_cmd}", (20, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)


def main():
    print("=== Android TV Gesture Remote ===")
    tv.init_tv()
    hands.init_hands()
    cap = camera.open_camera()

    last_cmd = None
    last_cmd_time = 0.0
    print("Camera active. Press 'q' or ESC in the video window to quit.")

    try:
        while True:
            cap, frame = camera.read_frame(cap)
            if frame is None:
                continue

            landmarks = hands.get_landmarks(frame)
            hands.draw_hand(frame, landmarks)

            action, status = gestures.update_gesture(landmarks)
            if action:
                last_cmd = action
                last_cmd_time = time.monotonic()
                print(f"[ACTION] {action}")
                tv.send_command(action)

            draw_hud(frame, status, last_cmd, last_cmd_time)
            cv2.imshow("Android TV Gesture Remote", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        camera.close_camera(cap)
        tv.close_tv()


if __name__ == "__main__":
    main()