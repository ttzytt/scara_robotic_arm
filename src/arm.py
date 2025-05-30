from src.motor_controller import TicMotorController
from src.kinematics import ParaScaraKinematics, ParaScaraSetup, ParaScaraState
from typing import Optional, Self, override
from src.utils import get_unsigned_ang_between
from src.consts import pqt, ur, DEF_LEN_UNIT
from math import pi
from abc import ABC, abstractmethod

class ArmWorkspaceChecker(ABC): 
    def __init__(self, setup: ParaScaraSetup): 
        self.setup = setup
        self.kine_solver = ParaScaraKinematics(setup)

    @abstractmethod
    def is_state_valid(self, state: ParaScaraState) -> bool:
        """ Check if the given state is in the workspace """

    @abstractmethod
    def is_pos_valid(self, x: pqt, y: pqt, mode: str = "+-") -> bool:
        """ Check if the given position of end effector is in the workspace """

class LinkAngleChecker(ArmWorkspaceChecker):
    def __init__(self, setup: ParaScaraSetup, threshold_ang: pqt = 7 * ur.deg):
        super().__init__(setup)
        self.threshold_ang = threshold_ang

    def get_link_ang_diff(self, state: ParaScaraState) -> pqt:
        """Compute the angle between the two links at a given state."""
        eff_x, eff_y = state.end_effector_pos
        l_x, l_y = state.lf_base_endpos
        r_x, r_y = state.rt_base_endpos

        vl_x = (eff_x - l_x).to(DEF_LEN_UNIT).m
        vl_y = (eff_y - l_y).to(DEF_LEN_UNIT).m
        vr_x = (eff_x - r_x).to(DEF_LEN_UNIT).m
        vr_y = (eff_y - r_y).to(DEF_LEN_UNIT).m

        ang = get_unsigned_ang_between(vl_x, vl_y, vr_x, vr_y) * ur.rad
        return ang % (2 * ur.pi) #type: ignore

    @override
    def is_state_valid(self, state: ParaScaraState) -> bool:
        """Return True if the link‐angle is far enough from straight (not stuck)."""
        ang_between = self.get_link_ang_diff(state)
        ang_diff = abs(ang_between - pi * ur.rad)
        return ang_diff >= self.threshold_ang

    @override
    def is_pos_valid(self, x: pqt, y: pqt, mode: str = "+-") -> bool:
        """Inverse‐kinematics then check the resulting state."""
        state = self.kine_solver.inverse_kinematics(x, y, mode)[0]
        return self.is_state_valid(state)

class NoChecker(ArmWorkspaceChecker):

    @override
    def is_state_valid(self, state: ParaScaraState) -> bool:
        # TODO: log warning here
        print("WARNING: No workspace checker is set, assuming all states are valid.")
        return True

    @override
    def is_pos_valid(self, x: pqt, y: pqt, mode: str = "+-") -> bool:
        # TODO: log warning here
        print("WARNING: No workspace checker is set, assuming all positions are valid.")
        return True

class CombinedChecker(ArmWorkspaceChecker):
    def __init__(self, *checkers: ArmWorkspaceChecker):
        if not checkers:
            raise ValueError("At least one checker must be provided.")
        self.checkers = checkers

    @override
    def is_state_valid(self, state: ParaScaraState) -> bool:
        return all(checker.is_state_valid(state) for checker in self.checkers)

    @override
    def is_pos_valid(self, x: pqt, y: pqt, mode: str = "+-") -> bool:
        return all(checker.is_pos_valid(x, y, mode) for checker in self.checkers)


class Arm:
    def __init__(
        self,
        setup: ParaScaraSetup,
        lf_motor: TicMotorController,
        rt_motor: TicMotorController,
        workspace_checker: Optional[ArmWorkspaceChecker] = None
    ):
            
        self.kine_solver = ParaScaraKinematics(setup)
        self.lf_motor = lf_motor
        self.rt_motor = rt_motor
        if workspace_checker is None:
            workspace_checker = NoChecker(setup) 
        self.workspace_checker = workspace_checker

    def reset_pos(self, x: pqt, y: pqt, mode: str = "+-"):
        state = self.kine_solver.inverse_kinematics(x, y, mode)[0]
        self.lf_motor.reset_pos(state.lf_base_ang.to(ur.deg).m)
        self.rt_motor.reset_pos(state.rt_base_ang.to(ur.deg).m)

    def reset_deg(self, left_deg: float, right_deg: float):
        self.lf_motor.reset_pos(left_deg)
        self.rt_motor.reset_pos(right_deg)

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

    def get_current_state(self, mode: str = 'o') -> list[ParaScaraState]:
        left_ang = self.lf_motor.get_current_deg()
        right_ang = self.rt_motor.get_current_deg()
        return self.kine_solver.forward_kinematics(
            left_ang * ur.deg, right_ang * ur.deg, mode
        )

    def is_moving(self) -> bool:
        return self.lf_motor.is_moving() or self.rt_motor.is_moving()

    def block_until_reach(self):
        while self.is_moving():
            pass

    def clean_up(self):
        self.lf_motor.tic.deenergize()
        self.rt_motor.tic.deenergize()

    def is_state_valid(self, state: ParaScaraState) -> bool:
        return self.workspace_checker.is_state_valid(state)

    def is_pos_valid(self, x: pqt, y: pqt, mode: str = "+-") -> bool:
        return self.workspace_checker.is_pos_valid(x, y, mode)
    
    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clean_up()