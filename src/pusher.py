from gpiozero import Servo
from src.consts import vec2f


class Pusher:
    def __init__(self, pin: int, servo_rg: vec2f, _reversed: bool = False) -> None:
        self.servo = Servo(pin)
        self.servo_rgp = servo_rg
        self.reversed = _reversed

    def map_to_servo_val(self, val: float) -> float:
        """ 
            map a value from 0, representing not pushed, to 1, representing fully pushed,
            to the servo's range of motion 
        """
        sl, sr = self.servo_rgp[0], self.servo_rgp[1]
        val = val if self.reversed else 1 - val
        return sl + (sr - sl) * val

    @property
    def pos(self) -> float:
        return self.servo.value

    @pos.setter
    def pos(self, value: float) -> None:
        self.servo.value = self.map_to_servo_val(value)

    def mid(self) -> None:
        """ Set the servo to the middle position. """
        self.pos = 0.5

    def min(self) -> None:
        """ Set the servo to the minimum position. """
        self.pos = 0.0
    def max(self) -> None:
        """ Set the servo to the maximum position. """
        self.pos = 1.0
    
    def retract(self) -> None:
        """ Retract the pusher to its minimum position. """
        self.min()
    
    def push(self) -> None:
        """ Push the pusher to its maximum position. """
        self.max()
