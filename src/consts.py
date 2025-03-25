import pint 
ur = pint.UnitRegistry()
from typing import Final, TypeAlias, Tuple

DEF_LEN_UNIT : Final = ur.mm
DEF_ANG_UNIT : Final = ur.deg
DEF_MASS_UNIT : Final = ur.g

tup_ff : TypeAlias = Tuple[float, float]
pqt: TypeAlias = pint.Quantity
tup_qq : TypeAlias = Tuple[pqt, pqt]