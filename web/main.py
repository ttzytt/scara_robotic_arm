# main.py
import json
import os
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from gpiozero import Motor
from web.gamepad import GamepadParser
from web.video import gen_frames
from web.response_manager import ResponseManager
from web.events import ConfirmRequestEvent, ConfirmResponseEvent
from src.mecanum_chassis import MecanumChassis
from src.motor_controller import I2CticMotorController, StepMode
from src.arm import ArmController
from src.consts import ur
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
parser = GamepadParser()

app = FastAPI()


from fastapi import WebSocket, WebSocketDisconnect
import asyncio, json


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager = ResponseManager(websocket)
    recv = manager.receive_loop()
    queue: asyncio.Queue[str] = asyncio.Queue()

    async def pump():
        async for raw_msg in recv:
            queue.put_nowait(raw_msg)

    pump_task = asyncio.create_task(pump())

    req1 = ConfirmRequestEvent(
        msg="Please move both motors to perpendicular position.", require_confirm="ok"
    )
    await manager.send_request(req1, ConfirmResponseEvent)
    resp1 = await manager.wait_for_response(req1)
    assert isinstance(resp1, ConfirmResponseEvent), "Expected ConfirmResponseEvent"
    print(f"Initialization step 1 confirmed: {resp1.response}")

    req2 = ConfirmRequestEvent(
        msg="Ready to start joystick control?", require_confirm="ok"
    )
    await manager.send_request(req2, ConfirmResponseEvent)
    resp2 = await manager.wait_for_response(req2)
    assert isinstance(resp2, ConfirmResponseEvent), "Expected ConfirmResponseEvent"
    print(f"Initialization step 2 confirmed: {resp2.response}")

    try:
        while True:
            raw_msg = await queue.get() 
            data = json.loads(raw_msg)
            meta, state = parser.parse_full(data)

            if not state.btn_rb.pressed:
                chassis.move(
                    x=-state.left_stick_y,  # forward/backward
                    y=state.left_stick_x,  # left/right
                    heading=state.right_stick_x,
                )
    except WebSocketDisconnect:
        pump_task.cancel()
        print("WebSocket disconnected")


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        gen_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
