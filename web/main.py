# main.py
import cv2
import json
import time

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from gpiozero import Motor
from gamepad import GamepadParser

# Motor and parser setup
test_motor = Motor(forward=15, backward=14, pwm=True)
parser     = GamepadParser()

app = FastAPI()

# Serve index.html and static assets
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return HTMLResponse(open("static/index.html").read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data: str = await websocket.receive_text()
            print("Received raw:", data)

            # Expecting full-gamepad JSON
            try:
                raw = json.loads(data)
            except json.JSONDecodeError:
                print("⚠️  Invalid JSON, ignoring")
                continue

            # Parse into typed meta + state
            meta, state = parser.parse_full(raw)
            print("GamepadMeta:", meta)
            print("GamepadState:", state)

            # Example motor control using left stick Y
            y = state.left_stick_y
            if y >  0.1:
                test_motor.forward(y)
            elif y < -0.1:
                test_motor.backward(abs(y))
            else:
                test_motor.stop()

    except WebSocketDisconnect:
        print("WebSocket disconnected")


def gen_frames():
    cap = None
    while True:
        if cap is None or not cap.isOpened():
            print("Attempting to connect to webcam…")
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS,          30)
            if not cap.isOpened():
                print("No camera—retrying in 2s…")
                cap.release()
                cap = None
                time.sleep(2)
                continue

        success, frame = cap.read()
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
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + jpg_bytes
            + b"\r\n"
        )


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        gen_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
