# web/main.py
import os
import json
import asyncio

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from web.gamepad import GamepadParser, GamepadState
from web.response_manager import ResponseManager
from web.events import ConfirmRequestEvent, ConfirmResponseEvent
from web.teleop import CombinedTeleop, ChassisTeleop, ArmTeleop, PusherTeleop
from web.video import gen_frames

from src.robot import DEFAULT_ROBOT  
from src.consts import ur

robot = DEFAULT_ROBOT  
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
print("Serving static files from:", STATIC_DIR)

teleop = CombinedTeleop(
    robot,
    ChassisTeleop(robot, coef=1.0),
    ArmTeleop(robot, start_pos=(0 * ur.mm, 100 * ur.mm), max_speed=20 * ur.mm),
    PusherTeleop(robot),
)

parser = GamepadParser()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    rmngr = ResponseManager(ws)
    recv = rmngr.receive_loop()
    queue: asyncio.Queue[str] = asyncio.Queue()

    async def pump():
        async for msg in recv:
            queue.put_nowait(msg)

    task = asyncio.create_task(pump())

    req1 = ConfirmRequestEvent(
        msg="Please move both motors to perpendicular position.", require_confirm="ok"
    )
    await rmngr.send_and_wait(req1)
    teleop.robot.arm.reset_deg(90, 90)
    print("deg reset to (90, 90)")

    req2 = ConfirmRequestEvent(
        msg="Ready to start joystick control?", require_confirm="ok"
    )
    await rmngr.send_and_wait(req2)  

    try:
        with robot as r:
            while True:
                raw = await queue.get()
                _, state = parser.parse_full(json.loads(raw))
                teleop.update(state)

    except WebSocketDisconnect:
        task.cancel()
        print("WebSocket disconnected")


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("web.main:app", host="raspberrypi.local", port=8000, reload=True)
