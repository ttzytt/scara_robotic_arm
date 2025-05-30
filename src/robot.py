from src.mecanum_chassis import MecanumChassis
from src.arm import ArmController
from src.motor_controller import TicMotorController
from consts import pqt, ur, vec2q
from typing import Callable, Optioanl

class Robot: 
    def __init__(self, chassis: MecanumChassis, arm: ArmController):
        self.chassis = chassis
        self.arm = arm
