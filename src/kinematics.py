from dataclasses import dataclass
from math import sin, cos, atan2, acos, asin, sqrt, pi, atan
from turtle import rt
from typing import List, TypeAlias
import pint
from pint._typing import QuantityOrUnitLike
from src.consts import *


@dataclass
class ParaScaraSetup:
    # the default of all unit should be in mm
    lf_base_len: pqt
    rt_base_len: pqt
    lf_link_len: pqt
    rt_link_len: pqt
    axis_dist: pqt

@dataclass
class ParaScaraState: 
    end_effector_pos : tup_qq
    lf_base_endpos   : tup_qq
    rt_base_endpos   : tup_qq

    lf_base_ang      : pqt
    rt_base_ang      : pqt
    lf_link_ang      : pqt
    rt_link_ang      : pqt

    def to_unit(self, dis_unit: QuantityOrUnitLike, ang_unit: QuantityOrUnitLike) -> "ParaScaraState":
        return ParaScaraState(
            (self.end_effector_pos[0].to(dis_unit), self.end_effector_pos[1].to(dis_unit)), # type: ignore
            (self.lf_base_endpos[0].to(dis_unit), self.lf_base_endpos[1].to(dis_unit)),     # type: ignore
            (self.rt_base_endpos[0].to(dis_unit), self.rt_base_endpos[1].to(dis_unit)),     # type: ignore
            (self.touching_pt_pos[0].to(dis_unit), self.touching_pt_pos[1].to(dis_unit)),   # type: ignore
            self.rt_link_ang.to(ang_unit), # type: ignore
            self.lf_base_ang.to(ang_unit), # type: ignore
            self.rt_base_ang.to(ang_unit), # type: ignore
            self.lf_link_ang.to(ang_unit), # type: ignore
        )


class ParaScaraKinematics:

    # refer to this paper: https://cdn.hackaday.io/files/1733257415536800/Educational%20Five-bar%20parallel%20robot_.pdf

    def __init__(self, setup: ParaScaraSetup):
        self.setup = setup

    def forward_kinematics(self, lf_base_ang: pqt, rt_base_ang: pqt) -> List[ParaScaraState]:
        l1: float = self.setup.lf_base_len.to(DEF_LEN_UNIT).magnitude
        l2: float = self.setup.lf_link_len.to(DEF_LEN_UNIT).magnitude
        l1p: float = self.setup.rt_base_len.to(DEF_LEN_UNIT).magnitude
        l2p: float = self.setup.rt_link_len.to(DEF_LEN_UNIT).magnitude
        d: float = self.setup.axis_dist.to(DEF_LEN_UNIT).magnitude
        q1: float = lf_base_ang.to(ur.rad).magnitude
        q2: float = rt_base_ang.to(ur.rad).magnitude

        A = 2 * l2p * l1p * sin(q2) - 2 * l1 * l2p * sin(q1)
        B = 2 * l2p * d - 2 * l1 * l2p * cos(q1) + 2 * l2p * l1p * cos(q2)

        # Example fix (assuming they should be plus):
        C = (
            l1**2 - l2**2 + l1p**2 + l2p**2 + d**2
            - 2*l1*l1p*sin(q1)*sin(q2)  
            - 2*l1*d*cos(q1) + 2*l1p*d*cos(q2)
            - 2*l1*l1p*cos(q1)*cos(q2) 
        )


        inside_sqrt = A**2 + B**2 - C**2
        solutions: List[ForwardSolution] = []  # type: ignore

        if inside_sqrt < 0:
            return solutions

        root_val = sqrt(inside_sqrt)
        for sign in (+1, -1):
            # sign is for the two possible solutions of theta 2
            rt_link_ang = 2 * atan2(A + sign * root_val, B - C)
            # rt_link_ang is the solution for theta 2
            num_asin = (
                l2p * sin(rt_link_ang)
                + l1p * sin(q2)
                - l1 * sin(q1)
            )   
            ratio = num_asin / l2

            if not (-1.0 <= ratio <= 1.0): return solutions

            for lf_link_ang_candidate in [asin(ratio), pi - asin(ratio)]:   
                # condiate is different solutions for theta 1
                x = l1 * cos(q1) + l2 * cos(lf_link_ang_candidate)
                y = l1 * sin(q1) + l2 * sin(lf_link_ang_candidate)  
                x_sol2 = d + l1p * cos(q2) + l2p * cos(rt_link_ang)
                y_sol2 = l1p * sin(q2) + l2p * sin(rt_link_ang)

                if abs(x - x_sol2) > 1e-10 or abs(y - y_sol2) > 1e-10: continue

                solutions.append(
                    ParaScaraState(
                        end_effector_pos=(x * DEF_LEN_UNIT, y * DEF_LEN_UNIT),
                        lf_base_endpos=(cos(lf_base_ang) * l1 * DEF_LEN_UNIT, sin(lf_base_ang) * l1 * DEF_LEN_UNIT),
                        rt_base_endpos=((cos(rt_base_ang) * l1p + d)* DEF_LEN_UNIT, sin(rt_base_ang) * l1p * DEF_LEN_UNIT),

                        lf_base_ang=lf_base_ang.to(DEF_ANG_UNIT), # type: ignore
                        rt_base_ang=rt_base_ang.to(DEF_ANG_UNIT), # type: ignore
                        lf_link_ang=(lf_link_ang_candidate * ur.rad).to(DEF_ANG_UNIT), # type: ignore
                        rt_link_ang=(rt_link_ang * ur.rad).to(DEF_ANG_UNIT), # type: ignore
                    )
                )

        return solutions


    def inverse_kinematics(self, x_pos: pqt, y_pos: pqt, mode: str | List[str] = "+-") -> List[ParaScaraState]:
        x: float = x_pos.to(DEF_LEN_UNIT).magnitude
        y: float = y_pos.to(DEF_LEN_UNIT).magnitude
        l1: float = self.setup.lf_base_len.to(DEF_LEN_UNIT).magnitude
        l1p: float = self.setup.rt_base_len.to(DEF_LEN_UNIT).magnitude
        l2: float = self.setup.lf_link_len.to(DEF_LEN_UNIT).magnitude
        l2p: float = self.setup.rt_link_len.to(DEF_LEN_UNIT).magnitude
        d: float = self.setup.axis_dist.to(DEF_LEN_UNIT).magnitude

        # cosine rule for the left arm
        c_val = sqrt(x**2 + y**2)
        theta = atan2(y, x)

        left = (-l2**2 + l1**2 + c_val**2) / (2 * l1 * c_val)
        if abs(left) > 1.0:
            raise ValueError("No real solution: left side arcs invalid.")
        gamma = acos(left)

        # cosine rule for the right arm
        e_val = sqrt((d - x)**2 + y**2)
        psi = atan2(y, (d - x))

        right = (-l2p**2 + l1p**2 + e_val**2) / (2 * l1p * e_val)
        if abs(right) > 1.0:
            raise ValueError("No real solution: right side arcs invalid.")
        epsilon = acos(right)

        # Ensure mode is a list of mode strings
        if isinstance(mode, str):
            modes = [mode]
        else:
            modes = mode

        results: List[ParaScaraState] = []
        for m in modes:
            if m not in ("++", "+-", "-+", "--"):
                raise ValueError(
                    f"Invalid mode '{m}' — must be one of '++', '+-', '-+', '--'")
            sign1 = 1 if m[0] == "+" else -1
            sign2 = 1 if m[1] == "+" else -1
            q1 = theta + sign1 * gamma
            q2 = pi - psi + sign2 * epsilon
            
            # TODO: add angle for second-level arm

            lf_base_endpos : tup_qq = (cos(q1) * l1 * DEF_LEN_UNIT, sin(q1) * l1 * DEF_LEN_UNIT)
            rt_base_endpos : tup_qq = ((cos(q2) * l1p + d) * DEF_LEN_UNIT, sin(q2) * l1p * DEF_LEN_UNIT)
            lf_link_ang = atan2(y - lf_base_endpos[1].magnitude, x - lf_base_endpos[0].magnitude)
            rt_link_ang = atan2(y - rt_base_endpos[1].magnitude, x - rt_base_endpos[0].magnitude)
            results.append(
                ParaScaraState(
                    end_effector_pos=(x_pos, y_pos),
                    lf_base_endpos=lf_base_endpos,
                    rt_base_endpos=rt_base_endpos,
                    lf_base_ang=(q1 * ur.rad).to(DEF_ANG_UNIT), # type: ignore
                    rt_base_ang=(q2 * ur.rad).to(DEF_ANG_UNIT), # type: ignore
                    lf_link_ang=(lf_link_ang * ur.rad).to(DEF_ANG_UNIT), # type: ignore
                    rt_link_ang=(rt_link_ang * ur.rad).to(DEF_ANG_UNIT), # type: ignore
                )
            )

        return results
