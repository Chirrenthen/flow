import time
import cv2
import config
import engine
import tv


def open_camera():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return cap


def draw_overlay(frame, status, last_cmd, last_cmd_time):
    h, w, _ = frame.shape
    mid_x, mid_y = w // 2, h // 2

    # 1. Draw 4-Quadrant Grid (Q1, Q2, Q3, Q4)
    cv2.line(frame, (mid_x, 52), (mid_x, h), (90, 90, 90), 1)
    cv2.line(frame, (0, mid_y), (w, mid_y), (90, 90, 90), 1)

    q_labels = [
        (1, "Q1", 15, 80),
        (2, "Q2", mid_x + 15, 80),
        (3, "Q3", mid_x + 15, mid_y + 30),
        (4, "Q4", 15, mid_y + 30),
    ]
    for q_id, text, lx, ly in q_labels:
        color = (0, 255, 255) if status["quadrant"] == q_id else (130, 130, 130)
        cv2.putText(frame, text, (lx, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

    # 2. hand landmarks
    landmarks = status["landmarks"]
    if landmarks:
        pts = [(int(x * w), int(y * h)) for x, y in landmarks]
        for a, b in engine.CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (0, 200, 100), 2)
        for idx, pt in enumerate(pts):
            radius = 7 if idx == 8 else 4
            col = (0, 255, 255) if idx == 8 else (255, 255, 255)
            cv2.circle(frame, pt, radius, col, -1)

    # index fingertip trail (point_history)
    trail = status["trail"]
    for i in range(1, len(trail)):
        p1 = (int(trail[i - 1][1] * w), int(trail[i - 1][2] * h))
        p2 = (int(trail[i][1] * w), int(trail[i][2] * h))
        thickness = max(1, int((i / len(trail)) * 6))
        cv2.line(frame, p1, p2, (0, 255, 255), thickness)

    # status banner
    banner_col = (25, 130, 25) if status["awake"] else (40, 40, 150)
    cv2.rectangle(frame, (0, 0), (w, 52), banner_col, -1)

    mode_str = f"POSE: {status['pose']}" if status["awake"] else "STANDBY (Hold Open Hand 1s)"
    cv2.putText(frame, mode_str, (15, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    # return guard
    if status["recentered_flash"]:
        cv2.putText(frame, "RETURN IGNORED (READY)", (w - 290, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)
    elif status["return_guard"]:
        guard_txt = f"Return Guard: Blocking {status['return_guard']}"
        cv2.putText(frame, guard_txt, (w - 310, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 215, 255), 2)

    # hold progress
    if status["progress"] > 0.05:
        bar_w = int(w * status["progress"])
        cv2.rectangle(frame, (0, 52), (bar_w, 60), (0, 255, 255), -1)

    # action trigger
    if last_cmd and (time.monotonic() - last_cmd_time < 0.9):
        cv2.putText(frame, f"SENT: {last_cmd}", (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 255, 255), 3)


def main():
    print("flow starting")
    tv.init_tv()
    engine.init_engine()
    cap = open_camera()

    last_cmd = None
    last_cmd_time = 0.0
    print("Ready, q to quit")

    try:
        while True:
            if cap is None or not cap.isOpened():
                time.sleep(1.0)
                cap = open_camera()
                continue

            ok, frame = cap.read()
            if not ok or frame is None:
                cap.release()
                time.sleep(0.5)
                cap = open_camera()
                continue

            # Mirror frame so moving your hand right moves right on the Quadrant grid
            frame = cv2.flip(frame, 1)

            action, status = engine.process_frame(frame)
            if action:
                last_cmd = action
                last_cmd_time = time.monotonic()
                print(f"[ACTION] {action}")
                tv.send_command(action)

            draw_overlay(frame, status, last_cmd, last_cmd_time)
            cv2.imshow("flow", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        tv.close_tv()


if __name__ == "__main__":
    main()
