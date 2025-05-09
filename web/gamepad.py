import json
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Union

# 1) Dataclasses

@dataclass
class GamepadBtn:
    pressed: bool
    value: float
    touched: bool

@dataclass
class GamepadState:
    left_stick_x: float
    left_stick_y: float
    right_stick_x: float
    right_stick_y: float
    left_trigger: Union[float, GamepadBtn]
    right_trigger: Union[float, GamepadBtn]
    btn_a: GamepadBtn
    btn_b: GamepadBtn
    btn_x: GamepadBtn
    btn_y: GamepadBtn
    btn_lb: GamepadBtn
    btn_rb: GamepadBtn
    btn_back: GamepadBtn
    btn_start: GamepadBtn
    dpad_up: GamepadBtn
    dpad_down: GamepadBtn
    dpad_left: GamepadBtn
    dpad_right: GamepadBtn

@dataclass
class GamepadMeta:
    id: str
    index: int
    timestamp: float
    connected: bool
    mapping: str


# 2) Default mapping for the “standard” layout
DefaultMapping: Dict[str, Dict[str, int]] = {
    "axes": {
        "left_stick_x": 0,
        "left_stick_y": 1,
        "right_stick_x": 2,
        "right_stick_y": 3,
    },
    "buttons": {
        "btn_a": 0,
        "btn_b": 1,
        "btn_x": 2,
        "btn_y": 3,
        "btn_lb": 4,
        "btn_rb": 5,
        "btn_back": 8,
        "btn_start": 9,
        "dpad_up": 12,
        "dpad_down": 13,
        "dpad_left": 14,
        "dpad_right": 15,
        # triggers on many gamepads come through as buttons:
        "left_trigger": 6,
        "right_trigger": 7,
    }
}


# 3) The parser
class GamepadParser:
    def __init__(self, mapping: Dict[str, Dict[str, int]] = DefaultMapping):
        self.ax_map  = mapping.get("axes", {})
        self.btn_map = mapping.get("buttons", {})

    def _parse_btn(self, raw: Any) -> Union[float, GamepadBtn]:
        if isinstance(raw, dict):
            return GamepadBtn(
                pressed=raw["pressed"],
                value=raw["value"],
                touched=raw["touched"]
            )
        return float(raw)

    def _parse_trigger(self,
                       axes: list[float],
                       buttons: list[dict],
                       name: str
                       ) -> Union[float, GamepadBtn]:
        # 1) Try axes first
        if name in self.ax_map:
            return float(axes[self.ax_map[name]])
        # 2) Then buttons
        if name in self.btn_map:
            return self._parse_btn(buttons[self.btn_map[name]])
        # 3) Fallback
        return 0.0

    def parse_full(self, raw: Dict[str, Any]) -> Tuple[GamepadMeta, GamepadState]:
        meta = GamepadMeta(
            id        = raw["id"],
            index     = raw["index"],
            timestamp = raw["timestamp"],
            connected = raw["connected"],
            mapping   = raw["mapping"],
        )
        axes    = raw["axes"]
        buttons = raw["buttons"]

        state = GamepadState(
            left_stick_x  = axes[self.ax_map["left_stick_x"]],
            left_stick_y  = axes[self.ax_map["left_stick_y"]],
            right_stick_x = axes[self.ax_map["right_stick_x"]],
            right_stick_y = axes[self.ax_map["right_stick_y"]],
            # <-- dynamic trigger parsing!
            left_trigger  = self._parse_trigger(axes, buttons, "left_trigger"),
            right_trigger = self._parse_trigger(axes, buttons, "right_trigger"),
            btn_a   = self._parse_btn(buttons[self.btn_map["btn_a"]]),
            btn_b   = self._parse_btn(buttons[self.btn_map["btn_b"]]),
            btn_x   = self._parse_btn(buttons[self.btn_map["btn_x"]]),
            btn_y   = self._parse_btn(buttons[self.btn_map["btn_y"]]),
            btn_lb  = self._parse_btn(buttons[self.btn_map["btn_lb"]]),
            btn_rb  = self._parse_btn(buttons[self.btn_map["btn_rb"]]),
            btn_back  = self._parse_btn(buttons[self.btn_map["btn_back"]]),
            btn_start = self._parse_btn(buttons[self.btn_map["btn_start"]]),
            dpad_up    = self._parse_btn(buttons[self.btn_map["dpad_up"]]),
            dpad_down  = self._parse_btn(buttons[self.btn_map["dpad_down"]]),
            dpad_left  = self._parse_btn(buttons[self.btn_map["dpad_left"]]),
            dpad_right = self._parse_btn(buttons[self.btn_map["dpad_right"]]),
        )

        return meta, state
