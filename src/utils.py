from src.consts import tup_ff
from math import sqrt, pi

def dist2d(a : tup_ff, b : tup_ff) -> float:
    return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def to_rad(deg : float) -> float:
    return deg * pi / 180

def to_deg(rad : float) -> float:
    return rad * 180 / pi