import time
import rp2

from machine import freq
from micropython import const

from aio_tcs3200 import TCS3200
from util import L298

freq(240000000)
right_cls = TCS3200(state_machine_id=0, out=0, s3=1, s2=2)
left_cls = TCS3200(state_machine_id=1, out=3, s3=4, s2=5)
left_drive = L298(en=16, in1=17, in2=18)
right_drive = L298(en=15, in1=14, in2=13)
half_speed = const(65535 // 2)
quarter_speed = const(65535 // 4)


def demo():
    time.sleep(5)

    left_drive.forward(quarter_speed)
    right_drive.forward(quarter_speed)
    time.sleep(2)

    left_drive.reverse(quarter_speed)
    right_drive.reverse(quarter_speed)
    time.sleep(2)

    left_drive.brake()
    right_drive.brake()
    time.sleep(1)

    left_drive.forward(half_speed)
    right_drive.forward(quarter_speed)
    time.sleep(2)

    left_drive.brake()
    right_drive.brake()
    time.sleep(1)

    while True:
        r, g, b = right_cls.rgb_raw()
        if r > 1.2 * g and r > 1.2 * b:
            left_drive.forward(half_speed)
            right_drive.reverse(half_speed)
            time.sleep(2)
            left_drive.brake()
            right_drive.brake()
            time.sleep(1)
            break


demo()

while True:
    time.sleep(2)
    # left_drive.reverse(const(65535 // 2))
    # time.sleep(2)
