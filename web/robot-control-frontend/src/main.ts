// src/main.ts

import "./style.css";
import {
    ConfirmRequestEvent,
    ConfirmResponseEvent,
    parseServerEvent,
    nextEid,
    GamepadRawState,
    GamepadBtn
} from "./events";

// ---------- WebSocket Setup ----------
const wsProtocol = location.protocol === "https:" ? "wss:" : "ws:";
const ws = new WebSocket(`${wsProtocol}//${location.host}/ws`);

ws.onopen = () => console.log("WebSocket connected");
ws.onclose = () => console.log("WebSocket disconnected");

/**
 * Handle incoming messages from server (ConfirmRequestEvent).
 * Since ConfirmRequestEvent extends ServerEvent, it already
 * has generated_t, eid, received_t filled by server.
 */
ws.onmessage = (ev) => {
    console.log("WebSocket message received:", ev.data);

    const req: ConfirmRequestEvent = parseServerEvent(ev.data);

    let ok: boolean;
    if (req.require_confirm === 'both') {
        ok = window.confirm(req.msg);
    } else if (req.require_confirm === 'ok') {
        do {
            ok = window.confirm(req.msg);
        } while (!ok);
    } else {
        do {
            ok = window.confirm(req.msg);
        } while (ok);
    }

    const resp: ConfirmResponseEvent = {
        name: 'confirm_response',
        generated_t: Date.now(),
        eid: nextEid(),
        respond_to_eid: req.eid,
        response: ok ? 'ok' : 'cancel'
    };

    ws.send(JSON.stringify(resp));
    console.log("WebSocket response sent:", resp);
};

// ---------- Gamepad Polling ----------
let gamepadIdx: number | null = null;

window.addEventListener("gamepadconnected", (e: GamepadEvent) => {
    gamepadIdx = e.gamepad.index;
    console.log("Gamepad connected:", e.gamepad.id);
});

window.addEventListener("gamepaddisconnected", () => {
    console.log("Gamepad disconnected");
    gamepadIdx = null;
});

/**
 * Continuously poll the connected gamepad and send its raw state 
 * to the server as GamepadRawState (a BrowserEvent).
 */
function pollGamepad() {
    if (gamepadIdx !== null && ws.readyState === WebSocket.OPEN) {
        const gpList = navigator.getGamepads();
        const gp = gpList[gamepadIdx];
        if (gp) {
            const buttons: GamepadBtn[] = gp.buttons.map((b) => ({
                pressed: b.pressed,
                value: b.value,
                touched: b.touched
            }));

            const evt: GamepadRawState = {
                name: 'gamepad_raw_state',
                generated_t: Date.now(),
                eid: nextEid(),
                id: gp.id,
                index: gp.index,
                axes: Array.from(gp.axes),
                buttons
            };

            ws.send(JSON.stringify(evt));
        }
    }
    requestAnimationFrame(pollGamepad);
}

requestAnimationFrame(pollGamepad);
