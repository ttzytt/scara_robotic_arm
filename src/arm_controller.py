from src.motor_controller import TicMotorController
from src.kinematics import *
from typing import Optional


class ArmController:
    def __init__(
        self,
        setup: ParaScaraSetup,
        lf_motor: TicMotorController,
        rt_motor: TicMotorController,
    ):
        self.setup = setup
        self.lf_motor = lf_motor
        self.rt_motor = rt_motor
        self.kine_solver = ParaScaraKinematics(setup)

    def reset_pos(self, x: pqt, y: pqt, mode: str = "+-"):
        state = self.kine_solver.inverse_kinematics(x, y, mode)[0]
        print(f"q1: {state.lf_base_ang}, q2: {state.rt_base_ang}")
        self.lf_motor.reset_pos(state.lf_base_ang.to(ur.deg).m)
        self.rt_motor.reset_pos(state.rt_base_ang.to(ur.deg).m)

    def move_to_pos(
        self, x: pqt, y: pqt, deg_per_sec: Optional[float] = None, mode: str = "+-"
    ):
        state = self.kine_solver.inverse_kinematics(x, y, mode)[0]
        print(f"q1: {state.lf_base_ang}, q2: {state.rt_base_ang}")
        self.lf_motor.move_to_angle_in_close_dir(
            state.lf_base_ang.to(ur.deg).m, deg_per_sec
        )
        self.rt_motor.move_to_angle_in_close_dir(
            state.rt_base_ang.to(ur.deg).m, deg_per_sec
        )

    def move_to_pos_blocking(
        self, x: pqt, y: pqt, deg_per_sec: Optional[float] = None, mode: str = "+-"
    ):
        self.move_to_pos(x, y, deg_per_sec, mode)
        self.block_until_reach()

    def is_moving(self):
        return self.lf_motor.is_moving() or self.rt_motor.is_moving()

    def block_until_reach(self):
        while self.is_moving():
            pass

    def clean_up(self): 
        self.lf_motor.tic.deenergize()
        self.rt_motor.tic.deenergize()