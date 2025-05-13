from src.motor_controller import TicMotorController
from src.kinematics import *
from typing import Optional
from src.utils import *

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
    
    def get_current_state(self, mode:str='o') -> List[ParaScaraState]: 
        left_ang = self.lf_motor.get_current_deg()
        right_ang = self.rt_motor.get_current_deg()
        return self.kine_solver.forward_kinematics(left_ang * ur.deg, right_ang * ur.deg, mode)
        

    def is_moving(self):
        return self.lf_motor.is_moving() or self.rt_motor.is_moving()

    def block_until_reach(self):
        while self.is_moving():
            pass

    def clean_up(self): 
        self.lf_motor.tic.deenergize()
        self.rt_motor.tic.deenergize()

    def check_link_stuck(self, threshold_ang : pqt = 7 * ur.deg, state : Optional[ParaScaraState] = None) -> bool:
        """ 
        For the two links, check if they're almost horizontal
        if they are, it means that the base won't be able to drive the arm 
        """
        if state is None:
            state = self.get_current_state('o')[0]
        eff_x, eff_y = state.end_effector_pos
        link_lx, link_ly = state.lf_base_endpos
        link_rx, link_ry = state.rt_base_endpos
        print("eff: ({}, {})".format(eff_x, eff_y))
        print("link_l: ({}, {})".format(link_lx, link_ly))
        print("link_r: ({}, {})".format(link_rx, link_ry))
        vl_x = (eff_x - link_lx).to(DEF_LEN_UNIT).m
        vl_y = (eff_y - link_ly).to(DEF_LEN_UNIT).m
        print("vl: ({}, {})".format(vl_x, vl_y))
        vr_x = (eff_x - link_rx).to(DEF_LEN_UNIT).m
        vr_y = (eff_y - link_ry).to(DEF_LEN_UNIT).m
        print("vr: ({}, {})".format(vr_x, vr_y))
        ang_between = get_unsigned_ang_between(vl_x, vl_y, vr_x, vr_y) * ur.rad % (2 * ur.pi)
        ang_diff = abs(ang_between - pi * ur.rad)
        print("ang_between: {}".format(ang_between.to(ur.deg)))
        print("ang_diff: {}".format(ang_diff.to(ur.deg)))
        return ang_diff < threshold_ang
    
    def check_link_stuck_if_moved_to(
        self, 
        x: pqt, 
        y: pqt, 
        threshold_ang : pqt = 10 * ur.deg, 
        mode: str = "+-"
    ) -> bool:
        state = self.kine_solver.inverse_kinematics(x, y, mode)[0]
        return self.check_link_stuck(threshold_ang, state)
    