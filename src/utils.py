from src.consts import tff
from math import sqrt

def dist2d(a : tff, b : tff) -> float:
    return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)