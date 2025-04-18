# main.py
import cv2
import asyncio
import io
import uvicorn
from fastapi import FastAPI, WebSocket, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

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
            data = await websocket.receive_text()
            # data now contains whatever key was pressed. For example, 'ArrowLeft', 'w', 'a', etc.
            # Do your control logic here, e.g. update motors or servo angles, etc.
            print("Received key:", data)

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
    """
    # Adjust the device index if needed
    cap = cv2.VideoCapture(0)
    # You might also set width, height, fps if needed:
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        raise RuntimeError("Could not open webcam.")

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Encode frame as JPEG
        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        jpg_bytes = buffer.tobytes()

        # Yield frame in multipart/x-mixed-replace format
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n")

    cap.release()


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
