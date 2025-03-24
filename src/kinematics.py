from dataclasses import dataclass
from math import sin, cos, atan2, acos, asin, sqrt, pi, atan
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


class ParaScaraKinematics:

    # refer to this paper: https://cdn.hackaday.io/files/1733257415536800/Educational%20Five-bar%20parallel%20robot_.pdf

    @dataclass
    class ForwardResult:
        x: pqt
        y: pqt
        lf_link_ang: pqt
        rt_link_ang: pqt

        def to(self, dis_unit: QuantityOrUnitLike, ang_unit: QuantityOrUnitLike) -> "ParaScaraKinematics.ForwardResult":
            return ParaScaraKinematics.ForwardResult(
                self.x.to(dis_unit),  # type: ignore
                self.y.to(dis_unit),  # type: ignore
                self.lf_link_ang.to(ang_unit),  # type: ignore
                self.rt_link_ang.to(ang_unit)  # type: ignore
            )

    @dataclass
    class InverseResult:
        lf_base_ang: pqt
        rt_base_ang: pqt

        def to(self, ang_unit: QuantityOrUnitLike) -> "ParaScaraKinematics.InverseResult":
            return ParaScaraKinematics.InverseResult(
                self.lf_base_ang.to(ang_unit),  # type: ignore
                self.rt_base_ang.to(ang_unit)   # type: ignore
            )

    def __init__(self, setup: ParaScaraSetup):
        self.setup = setup

    def forward_kinematics(self, lf_base_ang: pqt, rt_base_ang: pqt) -> List[ForwardResult]:
        ForwardSolution = ParaScaraKinematics.ForwardResult
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
            num_top = A + sign * root_val
            den = B - C

            if abs(den) < 1e-12:
                continue

            rt_link_ang = 2 * atan2(num_top, den)
            # rt_link_ang is the solution for theta 2

            num_asin = (
                l2p * sin(rt_link_ang)
                + l1p * sin(q2)
                - l1 * sin(q1)
            )   
            ratio = num_asin / l2

            if -1.0 <= ratio <= 1.0:
                for candidate in [asin(ratio), pi - asin(ratio)]:   
                    # condiate is different solutions for theta 1
                    x = l1 * cos(q1) + l2 * cos(candidate)
                    y = l1 * sin(q1) + l2 * sin(candidate)  
                    solutions.append(ForwardSolution(x * DEF_LEN_UNIT, y * DEF_LEN_UNIT,
                                        (candidate * ur.rad).to(DEF_ANG_UNIT),    # type: ignore
                                        (rt_link_ang * ur.rad).to(DEF_ANG_UNIT))) # type: ignore

        return solutions


    def inverse_kinematics(self, x_pos: pqt, y_pos: pqt, mode: str | List[str] = "+-") -> List[InverseResult]:
        InverseResult = ParaScaraKinematics.InverseResult
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

        results: List[InverseResult] = []
        for m in modes:
            if m not in ("++", "+-", "-+", "--"):
                raise ValueError(
                    f"Invalid mode '{m}' — must be one of '++', '+-', '-+', '--'")
            sign1 = 1 if m[0] == "+" else -1
            sign2 = 1 if m[1] == "+" else -1
            q1 = theta + sign1 * gamma
            q2 = pi - psi + sign2 * epsilon
            results.append(
                InverseResult(
                    (q1 * ur.rad).to(DEF_ANG_UNIT),  # type: ignore
                    (q2 * ur.rad).to(DEF_ANG_UNIT),  # type: ignore
                )
            )

        return results
