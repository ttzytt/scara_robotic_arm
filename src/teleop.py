from src.robot import Robot
from abc import ABC, abstractmethod
from web.gamepad import GamepadState

class TeleopController(ABC): 
    def __init__(self, robot: Robot):
        self.robot = robot
    
    @abstractmethod
    def update(self, gamepad_state: GamepadState) -> None:
        """Update the robot's state based on the gamepad input."""
        pass