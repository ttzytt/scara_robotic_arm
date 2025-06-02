import cv2
import time
from pyzbar.pyzbar import decode, ZBarSymbol


def gen_frames():
    cap = None
    detector_symbols = [ZBarSymbol.QRCODE]

    while True:
        check_cam_idxs = [0, 1, 2, 3]
        next_to_check_idx = 0

        # (Re-)connect the webcam if needed
        if cap is None or not cap.isOpened():
            print("Attempting to connect to webcam…")
            cap = cv2.VideoCapture(check_cam_idxs[next_to_check_idx])
            next_to_check_idx = (next_to_check_idx + 1) % len(check_cam_idxs)

            # Ask the camera to deliver MJPEG natively, reducing CPU work
            fourcc = cv2.VideoWriter.fourcc(*"MJPG")
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)

            if not cap.isOpened():
                print("No camera—retrying in .5s…")
                cap.release()
                cap = None
                time.sleep(0.5)
                continue

        success, frame = cap.read()
        if not success:
            print("Frame capture failed—reinit camera…")
            cap.release()
            cap = None
            continue

        # Flip the frame vertically and horizontally
        frame = cv2.flip(frame, 0)
        frame = cv2.flip(frame, 1)

        # 1) Use pyzbar to detect + decode QR codes in the frame
        decoded_objects = decode(frame, symbols=detector_symbols)

        for obj in decoded_objects:
            # obj.data is a byte string; decode to UTF-8
            data = obj.data.decode("utf-8")

            # obj.polygon is a list of Points (x, y)
            pts = [(point.x, point.y) for point in obj.polygon]

            # 2) Draw a green polygon around the QR code
            for i in range(len(pts)):
                pt1 = pts[i]
                pt2 = pts[(i + 1) % len(pts)]
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

            # 3) (Optional) Draw a blue bounding rectangle
            x, y, w, h = obj.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # 4) Overlay the decoded text near the QR code
            #    If there’s room above the box, place text above; otherwise below
            text_pos = (x, y - 10 if y - 10 > 10 else y + h + 20)
            cv2.putText(
                frame,
                data,
                text_pos,
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

        # 5) Re‐encode the frame as JPEG (quality = 70)
        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ret:
            print("JPEG encoding failed—skipping frame…")
            continue

        jpg_bytes = buffer.tobytes()

        # 6) Yield as part of an MJPEG stream:
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n")
