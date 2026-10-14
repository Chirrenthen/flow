import time
import cv2
import config


def open_camera():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return cap


def read_frame(cap):
    if cap is None or not cap.isOpened():
        time.sleep(1.0)
        cap = open_camera()
        return cap, None

    success, frame = cap.read()
    if not success or frame is None:
        cap.release()
        time.sleep(0.5)
        cap = open_camera()
        return cap, None

    # Mirror horizontally so swiping right moves right on screen
    return cap, cv2.flip(frame, 1)


def close_camera(cap):
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()