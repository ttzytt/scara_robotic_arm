from src.robot import Robot
from web.gamepad import GamepadState, GamepadBtn
from src.consts import vec2q, pqt, ur

from typing import override
from abc import ABC, abstractmethod
import time


class TeleopController(ABC):
    def __init__(self, robot: Robot):
        self.robot = robot

    @abstractmethod
    def update(self, gamepad_state: GamepadState) -> None:
        """Update the robot's state based on the gamepad input."""
        pass


class CombinedTeleop(TeleopController):
    def __init__(self, robot: Robot, *controllers: TeleopController):
        super().__init__(robot)
        self.controllers = controllers

    @override
    def update(self, gamepad_state: GamepadState) -> None:
        """Update all controllers with the gamepad state."""
        for controller in self.controllers:
            controller.update(gamepad_state)


class ArmTeleop(TeleopController):
    def __init__(self, robot: Robot, start_pos: vec2q, max_speed: pqt):
        super().__init__(robot)
        self.start_pos = start_pos
        self.max_speed = max_speed
        self.target_x, self.target_y = start_pos
        self.last_time = time.time()
        self.prev_state = self.robot.arm.get_current_state(mode="o")[0]
        self.moved_to_start = False

    @override
    def update(self, gamepad_state: GamepadState) -> None:
        st_time = time.time()
        if not gamepad_state.btn_lb.pressed and self.moved_to_start:
            return
        self.moved_to_start = True
        gamepad_state = gamepad_state.filter_deadzone(0.05)

        raw_x = gamepad_state.right_stick_x
        raw_y = -gamepad_state.right_stick_y

        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        dx = raw_x * self.max_speed * dt
        dy = raw_y * self.max_speed * dt

        new_x = self.target_x + dx
        new_y = self.target_y + dy
        assert isinstance(new_x, pqt) and isinstance(
            new_y, pqt
        ), "new_x and new_y must be pqt"
        try:
            if not self.robot.arm.is_pos_valid(new_x, new_y):
                print("not in the workspace")
                return
        except (IndexError, ValueError) as e:
            print("not in the workspace", e)
            print("last valid state", self.prev_state.to_unit(ur.mm, ur.deg))
            return

        self.target_x, self.target_y = new_x, new_y
        self.robot.arm.move_to_pos(self.target_x, self.target_y)

        ed_time = time.time()
        print("arm teleop update time: ", ed_time - st_time)
        try:
            self.prev_state = self.robot.arm.get_current_state(mode="oi")[0]
        except IndexError:
            pass


class ChassisTeleop(TeleopController):
    def __init__(self, robot: Robot, coef: float = 1.0):
        super().__init__(robot)
        self.coef = coef

    @override
    def update(self, gamepad_state: GamepadState) -> None:

        vx = -gamepad_state.left_stick_y * self.coef
        vy = gamepad_state.left_stick_x * self.coef
        h = gamepad_state.right_stick_x * self.coef

        if gamepad_state.btn_lb.pressed:
            h = 0.0  # prevent confict with arm control

        self.robot.chassis.move(vx, vy, h)


class PusherTeleop(TeleopController):

    @override
    def update(self, gamepad_state: GamepadState) -> None:
        assert isinstance(
            gamepad_state.right_trigger, (float, GamepadBtn)
        ), "right_trigger must be float or GamepadBtn"
        
        self.robot.pusher.pos = (
            gamepad_state.right_trigger
            if isinstance(gamepad_state.right_trigger, float)
            else gamepad_state.right_trigger.value
        )
