from src.mecanum_chassis import MecanumChassis
from src.arm_controller import ArmController
from src.motor_controller import TicMotorController
from dataclasses import dataclass

class Robot: 
    def __init__(self, chassis: MecanumChassis, arm: ArmController):
        self.chassis = chassis
        self.arm = arm
