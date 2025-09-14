import math 
from .constants import *
from numpy import float32 as fl

def mcsin(rad):
    if ANGLES == -1:
        return math.sin(rad)
    elif ANGLES == 65536:
        index = int(rad * fl(10430.378)) & 65535
    else:
        index = int(1 / (2 * PI) * ANGLES * rad) & (ANGLES - 1)
    return fl(math.sin(index * PI * 2.0 / ANGLES))

def mccos(rad):
    if ANGLES == -1:
        return math.cos(rad)
    elif ANGLES == 65536:
        index = int(rad * fl(10430.378) + fl(16384.0)) & 65535
    else:
        index = int(1 / (2 * PI) * ANGLES * rad + ANGLES / 4) & (ANGLES - 1)
    return fl(math.sin(index * PI * 2.0 / ANGLES))