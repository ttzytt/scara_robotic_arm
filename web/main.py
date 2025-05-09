# main.py
import cv2
import json
import time
import os
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from gpiozero import Motor
from web.gamepad import GamepadParser
from src.mecanum_chassis import MecanumChassis
from src.motor_controller import I2CticMotorController, StepMode
from src.arm_controller import ArmController
from src.consts import *
from src.kinematics import ParaScaraSetup

# Absolute path to the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Point at web/static, not just static
STATIC_DIR = os.path.join(BASE_DIR, "static")
print("Serving static files from:", STATIC_DIR)
# Motor and parser setup
lf_tp_motor = Motor(forward=15, backward=14, pwm=True)
rt_tp_motor = Motor(forward=24, backward=23, pwm=True)
rt_bt_motor = Motor(forward=25, backward=8, pwm=True)
lf_bt_motor = Motor(forward=7, backward=1, pwm=True)

lf_arm_motor = I2CticMotorController(1, 15, True, step_mode=StepMode._8)
rf_arm_motor = I2CticMotorController(1, 14, True, step_mode=StepMode._8)

setup = ParaScaraSetup(
    lf_base_len=85 * ur.mm,
    rt_base_len=85 * ur.mm,
    lf_link_len=85 * ur.mm,
    rt_link_len=85 * ur.mm,
    axis_dist=55 * ur.mm,
)
arm_controller = ArmController(setup, lf_arm_motor, rf_arm_motor)

chassis = MecanumChassis(
    lf_tp_motor=lf_tp_motor, rt_tp_motor=rt_tp_motor,
    lf_bt_motor=lf_bt_motor, rt_bt_motor=rt_bt_motor,
    lf_tp_motor_coef=1.0, rt_tp_motor_coef=1.0,
    lf_bt_motor_coef=1.0, rt_bt_motor_coef=1.0
)
parser     = GamepadParser()

app = FastAPI()

# Serve index.html and static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def root():

    return HTMLResponse(open(STATIC_DIR + "/index.html").read())


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

            lx_stick = state.left_stick_x
            ly_stick = state.left_stick_y
            rx_stick = state.right_stick_x
            ry_stick = state.right_stick_y
             
            if not state.btn_rb.pressed:
                chassis.move(
                    x=-ly_stick,  # Forward/backward
                    y=lx_stick,  # Left/right
                    heading=rx_stick 
                )
            # else: 
                # arm_state = arm_controller.get_current_state()[0]
                # cur_x, cur_y = arm_state.x.to(ur.mm).m, arm_state.y.to(ur.mm).m
                # COEF = 2
                # dx = COEF * rx_stick
                # dy = COEF * -ry_stick
                # arm_controller.move_to_pos(
                #     cur_x + dx * ur.mm, cur_y + dy * ur.mm
                # )
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
