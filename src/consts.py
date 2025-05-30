import pint 
ur = pint.UnitRegistry()
from typing import Final, TypeAlias

DEF_LEN_UNIT : Final = ur.mm
DEF_ANG_UNIT : Final = ur.deg
DEF_MASS_UNIT : Final = ur.g

vec2f : TypeAlias = tuple[float, float]
pqt: TypeAlias = pint.Quantity
vec2q : TypeAlias = tuple[pqt, pqt]