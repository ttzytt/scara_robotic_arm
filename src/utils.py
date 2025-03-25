from src.consts import tup_ff
from math import sqrt

def dist2d(a : tup_ff, b : tup_ff) -> float:
    return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)