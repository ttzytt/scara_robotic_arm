from dataclasses import dataclass

@dataclass 
class Gamepadbtn: 
    index : int
    pressed : bool
    value : float
    touched : bool

@dataclass
class GamepadState: 
    left_stick_x: float
    left_stick_y: float
    right_stick_x: float
    right_stick_y: float
    left_trigger: float
    right_trigger: float
    btn_a: bool
    btn_b: bool
    btn_x: bool
    btn_y: bool
    btn_lb: bool
    btn_rb: bool
    btn_start: bool
    btn_back: bool
    dpad_up: bool
    dpad_down: bool
    dpad_left: bool
    dpad_right: bool