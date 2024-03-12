import time

import micropython
from machine import freq
from micropython import const

from aio_tcs3200 import TCS3200
from util import L298, constrain

freq(240000000)
right_cls = TCS3200(state_machine_id=0, out=0, s3=1, s2=2)
left_cls = TCS3200(state_machine_id=1, out=3, s3=4, s2=5)
left_drive = L298(en=16, in1=17, in2=18)
right_drive = L298(en=15, in1=14, in2=13)
max_speed = const(65535)
half_speed = const(max_speed // 2)
quarter_speed = const(max_speed // 3)


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
        r, g, b, _ = right_cls.rgba_freq()
        if r > 1.2 * g and r > 1.2 * b:
            left_drive.forward(half_speed)
            right_drive.reverse(half_speed)
            time.sleep(2)
            left_drive.brake()
            right_drive.brake()
            time.sleep(1)
            break


def drive_past_start_line():
    r_init_min = 1
    r_init_max = 0
    for i in range(100):
        l, r = left_cls.val(TCS3200.RED), right_cls.val(TCS3200.RED)
        r_init_min = min(r_init_min, l, r)
        r_init_max = max(r_init_max, l, r)
    noise = r_init_max - r_init_min
    print(f"noise: {noise}")

    r_amb = (r_init_max + r_init_min) / 2
    print(f"r_amb: {r_amb}")
    left_drive.forward(quarter_speed)
    right_drive.forward(quarter_speed)

    while True:
        r = max(left_cls.val(TCS3200.RED), right_cls.val(TCS3200.RED))
        if r > r_amb + noise:
            print(f"start line r:{r}")
            break

    r_max = 0
    while True:
        r = max(left_cls.val(TCS3200.RED), right_cls.val(TCS3200.RED))
        if r < r_max - noise:
            break
        elif r > r_max:
            r_max = r
    print(f"r_max: {r_max}")

    left_drive.forward(0)
    right_drive.forward(0)
    # return gain
    return (r_max - r_amb) / 0.038, r_max, r_amb, noise


L = micropython.const(0.200)
V_MAX_MOTOR = micropython.const(1.3823 * 0.25)
W_MAX_MOTOR = micropython.const(2 * V_MAX_MOTOR / L)
K_P = micropython.const(140 * 1.2)
K_D = micropython.const(20 * 0)


def path_follow(r_red_val, l_red_val, gain, last_d, DEBUG=False):
    d = (r_red_val - l_red_val) / gain  # displacement from line in meters
    if last_d is None:
        dd = 0
    else:
        dd = d - last_d
    w = -constrain(K_P * d + K_D * dd, -W_MAX_MOTOR, W_MAX_MOTOR)
    if w > 0:
        v_right = V_MAX_MOTOR
        v_left = v_right - w * L
    else:
        v_left = V_MAX_MOTOR
        v_right = v_left + w * L
    pwm_right = int(v_right / V_MAX_MOTOR * quarter_speed)
    pwm_left = int(v_left / V_MAX_MOTOR * quarter_speed)
    if v_right > 0:
        right_drive.forward(pwm_right)
    else:
        right_drive.reverse(-pwm_right)
    if pwm_left > 0:
        left_drive.forward(pwm_left)
    else:
        left_drive.reverse(-pwm_left)
    if DEBUG:
        print("d:", d)
        print("dd:", dd)
        print("w:", w)
        print("v(r,l):", v_right, v_left)
        print("pwm(r,l):", pwm_right, pwm_left)
        time.sleep_ms(1)
    return d


def is_off_path(r_red_val, l_red_val, r_amb, noise) -> bool:
    if r_red_val < r_amb + noise and l_red_val < r_amb + noise:
        return True
    return False


DEBUG = False
if __name__ == "__main__":
    # GAIN, RED_MAX, RED_AMB, NOISE = 5.3, 0.5, 0.3, 0.001
    time.sleep(5)
    GAIN, RED_MAX, RED_AMB, NOISE = drive_past_start_line()
    last_d = None
    while True:
        red_r, red_l = right_cls.val(TCS3200.RED), left_cls.val(TCS3200.RED)
        if is_off_path(red_r, red_l, RED_AMB, NOISE):
            left_drive.brake()
            right_drive.brake()
            time.sleep_ms(1000)
            continue
        last_d = path_follow(red_r, red_l, GAIN, last_d, DEBUG)
        time.sleep_ms(1)


while True:
    time.sleep(2)
