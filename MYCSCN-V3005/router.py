# router.py
from enum import IntEnum

class Route(IntEnum):
    LANDING = 0
    SCAN    = 1
    HISTORY = 2
    SCAN_DETAIL = 3
    SERVO_CONTROL = 4

def goto(stack, route: Route):
    stack.setCurrentIndex(int(route))
