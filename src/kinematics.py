from dataclasses import dataclass
from math import sin, cos, atan2, acos, asin, sqrt, pi
from typing import List, Type


class ParaScaraKinematics:
   
    # refer to this paper: https://cdn.hackaday.io/files/1733257415536800/Educational%20Five-bar%20parallel%20robot_.pdf
   
    @dataclass
    class ParaScaraKinematicsCfg:
        lf_base_len: float
        rt_base_len: float
        lf_link_len: float
        rt_link_len: float
        axis_dist: float

    @dataclass
    class ForwardSolution:
        x: float
        y: float
        lf_link_ang: float
        rt_link_ang: float

    @dataclass
    class InverseResult:
        lf_base_ang: float
        rt_base_ang: float
    
    def __init__(self, cfg: ParaScaraKinematicsCfg):
        self.cfg = cfg

    def forward_kinematics(self, lf_base_ang: float, rt_base_ang: float) -> List[ForwardSolution]:
        ForwardSolution = ParaScaraKinematics.ForwardSolution
        l1  = self.cfg.lf_base_len
        l2  = self.cfg.lf_link_len
        l1p = self.cfg.rt_base_len
        l2p = self.cfg.rt_link_len
        d   = self.cfg.axis_dist
        q1  = lf_base_ang
        q2  = rt_base_ang

        A = 2 * l2p * l1p * sin(q2) - 2 * l1 * l2p * cos(q1)
        B = 2 * l2p * d - 2 * l1 * l2p * cos(q1) + 2 * l2 * l1p * cos(q2)
        C = (
            l1**2 - l2**2 + l1p**2 + l2p**2 + d**2
            - l1 * l1p * sin(q1) * sin(q2)
            - 2 * l1 * d * cos(q1) + 2 * l1p * d * cos(q2)
            - 2 * l1 * l1p * cos(q1) * cos(q2)
        )

        inside_sqrt = A**2 + B**2 - C**2
        solutions: List[ForwardSolution] = [] #type:ignore

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
                    solutions.append(ForwardSolution(x, y, candidate, rt_link_ang))

        return solutions

    def inverse_kinematics(self, x: float, y: float, mode: str) -> InverseResult:
        InverseResult = ParaScaraKinematics.InverseResult
        l1 = self.cfg.lf_base_len
        l2 = self.cfg.lf_link_len
        d  = self.cfg.axis_dist

        # cosine rule for the left arm
        c_val = sqrt(x**2 + y**2)
        theta = atan2(y, x)

        left = (-l2**2 + l1**2 + c_val**2) / (2 * l1 * c_val)
        if abs(left) > 1.0:
            raise ValueError("No real solution: left side arcs invalid.")
        gamma = acos(left)

        # cosine rule for the right arm
        e = sqrt((d - x)**2 + y**2)
        psi = atan2(y, (d - x))

        right = (-l2**2 + l1**2 + e**2) / (2 * l1 * e)
        if abs(right) > 1.0:
            raise ValueError("No real solution: right side arcs invalid.")
        epsilon = acos(right)

        assert mode in ("++", "+-", "-+", "--")
        sign1 = 1 if mode[0] == "+" else -1
        sign2 = 1 if mode[1] == "+" else -1
        q1 = theta + sign1 * gamma
        q2 = pi - psi + sign2 * epsilon

        return InverseResult(q1, q2)
