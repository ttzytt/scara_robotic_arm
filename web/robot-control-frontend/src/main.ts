import "./style.css";

// ---------- WebSocket ----------
const wsProtocol = location.protocol === "https:" ? "wss:" : "ws:";
const ws = new WebSocket(`${wsProtocol}//${location.host}/ws`);

ws.onopen = () => console.log("WebSocket connected");
ws.onmessage = e => console.log("From Pi:", e.data);
ws.onclose = () => console.log("WebSocket disconnected");

// ---------- Gamepad ----------
let gamepadIdx: number | null = null;

window.addEventListener("gamepadconnected", (e) => {
  gamepadIdx = e.gamepad.index;
  console.log("Gamepad connected:", e.gamepad.id);
});

window.addEventListener("gamepaddisconnected", () => {
  console.log("Gamepad disconnected");
  gamepadIdx = null;
});

function pollGamepad() {
  if (gamepadIdx !== null && ws.readyState === WebSocket.OPEN) {
    const gp = navigator.getGamepads()[gamepadIdx];
    if (gp) {
      const payload = {
        id: gp.id,
        index: gp.index,
        timestamp: gp.timestamp,
        connected: gp.connected,
        mapping: gp.mapping,
        axes: Array.from(gp.axes),
        buttons: gp.buttons.map((b, i) => ({
          index: i,
          pressed: b.pressed,
          value: b.value,
          touched: b.touched
        }))
      };
      ws.send(JSON.stringify(payload));
    }
  }
  requestAnimationFrame(pollGamepad);
}
requestAnimationFrame(pollGamepad);
