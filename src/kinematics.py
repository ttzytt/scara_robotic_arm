from dataclasses import dataclass
from math import sin, cos, atan2, acos, asin, sqrt, pi, atan
from typing import List, TypeAlias
from pint._typing import QuantityOrUnitLike
from src.consts import *
from src.utils import *

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

    def forward_kinematics(
        self,
        lf_base_ang: pqt,
        rt_base_ang: pqt,
        mode: str = "o"   # allowed values: "i", "o", "io", "oi"
    ) -> List[ParaScaraState]:
        """
        Compute the end‐effector states for given base angles.
        mode:
          "i"  → inward only  (smaller opening angle)
          "o"  → outward only (larger opening angle)
          "io" → inward then outward
          "oi" → outward then inward
        """
        if mode not in ("i", "o", "io", "oi"):
            raise ValueError("mode must be one of 'i','o','io','oi'")

        # 1) unpack lengths & angles (in DEF_LEN_UNIT / radians)
        l1   = self.setup.lf_base_len .to(DEF_LEN_UNIT).magnitude
        l2   = self.setup.lf_link_len .to(DEF_LEN_UNIT).magnitude
        l1p  = self.setup.rt_base_len .to(DEF_LEN_UNIT).magnitude
        l2p  = self.setup.rt_link_len .to(DEF_LEN_UNIT).magnitude
        d    = self.setup.axis_dist   .to(DEF_LEN_UNIT).magnitude
        q1   = lf_base_ang.to(ur.rad).magnitude
        q2   = rt_base_ang.to(ur.rad).magnitude

        # 2) compute elbow pivots
        x1 = l1 * cos(q1)
        y1 = l1 * sin(q1)
        x2 = d  + l1p * cos(q2)
        y2 =     l1p * sin(q2)

        # 3) circle–circle intersection
        dx = x2 - x1
        dy = y2 - y1
        R  = sqrt(dx*dx + dy*dy)
        if R > (l2 + l2p) or R < abs(l2 - l2p):
            return []  # no real solution

        a  = (l2*l2 - l2p*l2p + R*R) / (2 * R)
        h2 = max(0.0, l2*l2 - a*a)
        h  = sqrt(h2)
        xm = x1 + a * dx / R
        ym = y1 + a * dy / R

        # 4) build both raw solutions
        raw = []
        for sign in (+1, -1):
            xi = xm + sign * h * ( dy / R)
            yi = ym - sign * h * ( dx / R)

            state = ParaScaraState(
                end_effector_pos=(xi * DEF_LEN_UNIT, yi * DEF_LEN_UNIT),
                lf_base_endpos   =(x1 * DEF_LEN_UNIT, y1 * DEF_LEN_UNIT),
                rt_base_endpos   =(x2 * DEF_LEN_UNIT, y2 * DEF_LEN_UNIT),
                lf_base_ang      =lf_base_ang.to(DEF_ANG_UNIT),                  # type: ignore
                rt_base_ang      =rt_base_ang.to(DEF_ANG_UNIT),                  # type: ignore
                lf_link_ang      =(atan2(yi - y1, xi - x1) * ur.rad).to(DEF_ANG_UNIT),  # type: ignore
                rt_link_ang      =(atan2(yi - y2, xi - x2) * ur.rad).to(DEF_ANG_UNIT),  # type: ignore
            )
            raw.append((xi, yi, state))

        # 5) compute opening‐angle for each solution
        phis = []
        for xi, yi, _ in raw:
            v1x, v1y = -x1, -y1
            v2x, v2y = xi - x1, yi - y1
            phi = get_unsigned_ang_between(v1x, v1y, v2x, v2y)
            phis.append(phi)

        # 6) sort indices by phi: smaller→inward, larger→outward
        indices = sorted(range(2), key=lambda i: phis[i])
        tag_state = {
            "i": raw[indices[0]][2],
            "o": raw[indices[1]][2],
        }

        # 7) assemble results in requested mode order
        result: List[ParaScaraState] = []
        for ch in mode:
            result.append(tag_state[ch])
        return result

    def inverse_kinematics(self, x_pos: pqt, y_pos: pqt, mode: str | List[str] = "+-") -> List[ParaScaraState]:
        mode = mode or ["+-"]
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
