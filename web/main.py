# main.py
import cv2
import asyncio
import io
import uvicorn
from fastapi import FastAPI, WebSocket, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
import time
from gpiozero import Motor
from parse import parse


test_motor = Motor(forward=15, backward=14, pwm=True)

app = FastAPI()

# Mount static files, so we can serve index.html from /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global store for connected websockets (so you can manage multiple clients, if needed)
active_websockets = set()


@app.get("/")
async def root():
    # Just redirect to our static index.html
    return HTMLResponse(content=open("static/index.html").read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept websocket connection
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        while True:
            # We wait for a message from the client (the keystrokes).
            data : str = await websocket.receive_text()
            # data now contains whatever key was pressed. For example, 'ArrowLeft', 'w', 'a', etc.
            # Do your control logic here, e.g. update motors or servo angles, etc.
            print("Received key:", data)

            if data.startswith("stick"):
                result = parse("stick:{side}:{x:f},{y:f}", data)
                print("parse result: ", result)

                if result['side'] == 'left': 
                    if result['y'] > 0.1:
                        test_motor.forward(abs(result['y']))
                    elif result['y'] < -0.1:
                        test_motor.backward(abs(result['y']))
                    else: 
                        test_motor.stop()

            # Optionally, you can also send back a message to client
            # await websocket.send_text(f"Got key: {data}")
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        active_websockets.remove(websocket)



def gen_frames():
    """
    Generator function to capture frames from the Pi camera (or any webcam)
    and yield them as JPEG bytes for a multipart streaming response (MJPEG).
    Automatically attempts to reconnect if the camera fails.
    """
    cap = None

    while True:
        # Initialize/reinitialize camera if not already available
        if cap is None or not cap.isOpened():
            print("Attempting to connect to webcam...")
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)

            if not cap.isOpened():
                print("Webcam not found. Retrying in 2 seconds...")
                cap.release()
                cap = None
                time.sleep(2)
                continue

        success, frame = cap.read()

        if not success:
            print("Frame capture failed. Reinitializing camera...")
            cap.release()
            cap = None
            continue

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            print("JPEG encoding failed. Skipping frame.")
            continue

        jpg_bytes = buffer.tobytes()

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n")



@app.get("/video_feed")
def video_feed():
    """
    Route that streams webcam frames as MJPEG.
    The client can embed this route in an <img> or <video> tag.
    """
    return StreamingResponse(
        gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
