from dataclasses import dataclass, replace
from dataclasses_json import DataClassJsonMixin
from web.events import BrowserEvent
from typing import Self, Any


@dataclass(kw_only=True)
class GamepadBtn(DataClassJsonMixin):
    pressed: bool
    value: float
    touched: bool

@dataclass(kw_only=True)
class GamepadRawState(BrowserEvent):
    name: str = "gamepad_raw_state"
    id: str
    index: int
    axes: list[float]
    buttons: list[GamepadBtn]

DEFAULT_GPAD_MAPPING: dict[str, dict[str, int]] = {
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

@dataclass(kw_only=True)
class GamepadState:
    left_stick_x: float
    left_stick_y: float
    right_stick_x: float
    right_stick_y: float
    left_trigger: GamepadBtn
    right_trigger: GamepadBtn
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

    @classmethod
    def from_raw(
        cls, raw_state: GamepadRawState, mapping: dict[str, dict[str, int]] = DEFAULT_GPAD_MAPPING
    ) -> Self:
        values: dict[str, Any] = {}

        axes_map = mapping.get("axes", {})
        for axis_name, axis_index in axes_map.items():
            if axis_index < 0 or axis_index >= len(raw_state.axes):
                raise IndexError(f"axes index {axis_index} out of range")
            values[axis_name] = float(raw_state.axes[axis_index])

        btn_map = mapping.get("buttons", {})
        for btn_name, btn_index in btn_map.items():
            if btn_index < 0 or btn_index >= len(raw_state.buttons):
                raise IndexError(f"buttons index {btn_index} out of range")
            values[btn_name] = raw_state.buttons[btn_index]

        return cls(**values)

    def filter_deadzone(self, deadzone: float = 0.05) -> Self:
        return replace(
            self,
            left_stick_x=self.left_stick_x if abs(self.left_stick_x) > deadzone else 0.0,
            left_stick_y=self.left_stick_y if abs(self.left_stick_y) > deadzone else 0.0,
            right_stick_x=self.right_stick_x if abs(self.right_stick_x) > deadzone else 0.0,
            right_stick_y=self.right_stick_y if abs(self.right_stick_y) > deadzone else 0.0,
        )