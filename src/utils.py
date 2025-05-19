from src.consts import tup_ff
from math import sqrt, pi, atan2, acos
from time import time

def dist2d(a : tup_ff, b : tup_ff) -> float:
    return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def to_rad(deg : float) -> float:
    return deg * pi / 180

def to_deg(rad : float) -> float:
    return rad * 180 / pi

def clamp(val : float, min_val : float, max_val : float) -> float:
    return max(min_val, min(val, max_val))

def get_signed_ang_between(v1x : float, v1y : float, v2x : float, v2y : float) -> float:
    """
    Get the signed angle between two vectors in radians.
    """
    dot = v1x * v2x + v1y * v2y
    det = v1x * v2y - v1y * v2x
    return atan2(det, dot)

def get_unsigned_ang_between(v1x : float, v1y : float, v2x : float, v2y : float) -> float:
    """
    Get the unsigned angle between two vectors in radians.
    """
    dot = v1x * v2x + v1y * v2y
    norm1 = sqrt(v1x * v1x + v1y * v1y)
    norm2 = sqrt(v2x * v2x + v2y * v2y)
    return acos(clamp(dot / (norm1 * norm2), -1.0, 1.0))

def get_time_millis() -> int:
    return round(time() * 1000)