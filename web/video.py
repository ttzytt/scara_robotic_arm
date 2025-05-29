import cv2
import time
def gen_frames():
    cap = None
    while True:
        check_cam_idxs = [0, 1, 2, 3]
        next_to_check_idx = 0
        if cap is None or not cap.isOpened():
            print("Attempting to connect to webcam…")
            cap = cv2.VideoCapture(check_cam_idxs[next_to_check_idx])
            next_to_check_idx += 1
            next_to_check_idx %= len(check_cam_idxs)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            if not cap.isOpened():
                print("No camera—retrying in .5s…")
                cap.release()
                cap = None
                time.sleep(0.5)
                continue

        success, frame = cap.read()

        # flip it vertically

        frame = cv2.flip(frame, 0)
        if not success:
            print("Frame capture failed—reinit camera…")
            cap.release()
            cap = None
            continue

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            print("JPEG encoding failed, skipping frame…")
            continue

        jpg_bytes = buffer.tobytes()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n")
