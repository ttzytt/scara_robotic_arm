from dataclasses import dataclass
from numpy import diff
from kinematics import ParaScaraSetup
import pymunk as pmk
from typing import Tuple, TypeAlias
from src.consts import *
from src.utils import *
from math import atan2, sqrt

@dataclass 
class ParaScaraPhySpecs:
    base_arm_mass     : pqt
    base_arm_wid      : pqt
    link_arm_mass     : pqt
    link_arm_wid      : pqt
    end_effector_mass : pqt


class ParaScaraSim:
    def __init__(self, setup: ParaScaraSetup, phy: ParaScaraPhySpecs, lf_motor_pos : Tuple[float, float] = (0, 0)):

        r"""
            initial setup: 
                    x <-- link touching point
                   / \
                  /   \
                  x   x <-- link and base connecting point
                  |   |
                  |   |
                  x   x <-- motor axis
        """

        axis_dist = setup.axis_dist.to(DEF_LEN_UNIT).magnitude
        
        base_arm_mass = phy.base_arm_mass.to(DEF_MASS_UNIT).magnitude
        base_arm_wid = phy.base_arm_wid.to(DEF_LEN_UNIT).magnitude
        lf_base_len = setup.lf_base_len.to(DEF_LEN_UNIT).magnitude
        rt_base_len = setup.rt_base_len.to(DEF_LEN_UNIT).magnitude

        link_arm_mass = phy.link_arm_mass.to(DEF_MASS_UNIT).magnitude
        link_arm_wid = phy.link_arm_wid.to(DEF_LEN_UNIT).magnitude
        lf_link_len = setup.lf_link_len.to(DEF_LEN_UNIT).magnitude
        rt_link_len = setup.rt_link_len.to(DEF_LEN_UNIT).magnitude

        end_effector_mass = phy.end_effector_mass.to(DEF_MASS_UNIT).magnitude

        self.setup = setup
        self.space = pmk.Space()
        self.space.gravity = (0.0, 0.0) # gravity in z-axis so can't specify here
        self.lf_motor_body = pmk.Body(body_type=pmk.Body.KINEMATIC)
        self.rt_motor_body = pmk.Body(body_type=pmk.Body.KINEMATIC)

        self.lf_motor_body.position = lf_motor_pos
        rt_motor_pos = (lf_motor_pos[0] + axis_dist, lf_motor_pos[1])
        self.rt_motor_body.position = rt_motor_pos

        self.lf_base_body, self.lf_base_shape = self.gen_vert_arm(base_arm_wid, lf_base_len, lf_motor_pos, base_arm_mass)

        self.rt_base_body, self.rt_base_shape = self.gen_vert_arm(base_arm_wid, rt_base_len, rt_motor_pos, base_arm_mass)

        link_touch_pt = (
            (lf_motor_pos[0] + rt_motor_pos[0]) / 2
            
        )

    @staticmethod 
    def gen_vert_arm(wid : float, len_ : float, lower_end_pos: tup_ff , mass : float) -> Tuple[pmk.Body, pmk.Shape]:
        moment = pmk.moment_for_box(mass, (wid, wid))
        body = pmk.Body(mass, moment, body_type=pmk.Body.DYNAMIC)
        shape = pmk.Poly.create_box(body, (wid, len_))
        body.position = (lower_end_pos[0], lower_end_pos[1] + len_/2)
        return body, shape
    
    @staticmethod
    def gen_arm_connecting(a : tup_ff, b : tup_ff, mass : float, wid : float) -> Tuple[pmk.Body, pmk.Shape]:
        moment = pmk.moment_for_box(mass, (wid, wid))
        body = pmk.Body(mass, moment, body_type=pmk.Body.DYNAMIC)
        len_ = dist2d(a, b)
        diff_y = b[1] - a[1]
        diff_x = b[0] - a[0]
        ang = atan2(diff_y, diff_x)
        body.ang = ang 
        body.position = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        shape = pmk.Poly.create_box(body, (wid, len_))
        return body, shape