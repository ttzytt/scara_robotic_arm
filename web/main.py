import os
import asyncio
import time

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from web.gamepad import GamepadRawState, GamepadState, DEFAULT_GPAD_MAPPING
from web.comm_helper import CommHelper
from web.events import ConfirmRequestEvent
from web.teleop import CombinedTeleop, ChassisTeleop, ArmTeleop, PusherTeleop
from web.video import gen_frames

from src.robot import DEFAULT_ROBOT
from src.consts import ur
from icecream import ic

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
print("Serving static files from:", STATIC_DIR)


# Create the robot and teleop controllers
robot = DEFAULT_ROBOT
teleop = CombinedTeleop(
    robot,
    ChassisTeleop(robot, coef=1.0),
    ArmTeleop(robot, start_pos=(0 * ur.mm, 100 * ur.mm), max_speed=200.0 * ur.mm),
    PusherTeleop(robot),
)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    rmngr = CommHelper(ws)
    recv_task = asyncio.create_task(rmngr.receive_loop())

    req1 = ConfirmRequestEvent(
        msg="Please move both motors to perpendicular position.", require_confirm="ok"
    )
    await rmngr.send_and_wait(req1)
    teleop.robot.arm.reset_deg(90, 90)
    print("Arm reset to (90, 90)")

    req2 = ConfirmRequestEvent(
        msg="Ready to start joystick control?", require_confirm="ok"
    )
    await rmngr.send_and_wait(req2)
    print("Joystick control ready")
    try:
        with robot:
            while True:
                start_time = time.time()

                raw_json = await rmngr.pop_latest(GamepadRawState)
                try:
                    raw_state = GamepadRawState.deserialize(raw_json)
                except Exception:
                    print("Ignored non-gamepad event:", raw_json)
                    continue
                print("Gamepad latency (ms):", raw_state.latency)
                gs = GamepadState.from_raw(raw_state, DEFAULT_GPAD_MAPPING)
                teleop.update(gs)
                
                end_time = time.time()
                print(f"Main loop processed in {end_time - start_time:.4f} seconds")

    except WebSocketDisconnect:
        recv_task.cancel()
        print("WebSocket disconnected")


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("web.main:app", host="raspberrypi.local", port=8000, reload=True)
