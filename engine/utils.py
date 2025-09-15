import math 
from .constants import *
from numpy import float32 as fl

def mcsin(rad):
    if ANGLES == 65536:
        index = int(rad * fl(10430.378)) & 65535
        return fl(math.sin(index * math.pi * 2.0 / 65536))
    else:
        return math.sin(rad)

def mccos(rad):
    if ANGLES == 65536:
        index = int(rad * fl(10430.378) + fl(16384.0)) & 65535
        return fl(math.sin(index * math.pi * 2.0 / 65536))
    else:
        return math.cos(rad)