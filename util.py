from machine import PWM, Pin
from micropython import const


def constrain(val, a, b):
    return min(max(val, min(a, b)), b)


class Servo:
    __servo_pwm_freq = 50
    __min_u16_duty = const(1640 - 2)  # offset for correction
    __max_u16_duty = const(7864 - 0)  # offset for correction
    min_angle = 0
    max_angle = 180
    current_angle = 0

    def __init__(self, pin: int):
        self.__angle_conversion_factor = (
            self.__max_u16_duty - self.__min_u16_duty
        ) // (self.max_angle - self.min_angle)
        self.__motor = PWM(Pin(pin))
        self.__motor.freq(self.__servo_pwm_freq)

    def move(self, angle: int):
        if angle == self.current_angle:
            return
        self.current_angle = angle
        # calculate the new duty cycle and move the motor
        duty_u16 = (
            (angle - self.min_angle) * self.__angle_conversion_factor
        ) + self.__min_u16_duty
        self.__motor.duty_u16(duty_u16)


class L298(object):
    def __init__(self, en, in1, in2, freq=1000):
        self._p_en = PWM(Pin(en, Pin.OUT), freq=freq, duty_u16=0)
        self._p_in1 = Pin(in1, Pin.OUT)
        self._p_in2 = Pin(in2, Pin.OUT)

    def brake(self):
        self._p_en.duty_u16(65535)
        self._p_in1.low()
        self._p_in2.low()

    def forward(self, duty_u16):
        self._p_en.duty_u16(duty_u16)
        self._p_in1.high()
        self._p_in2.low()

    def reverse(self, duty_u16):
        self._p_en.duty_u16(duty_u16)
        self._p_in1.low()
        self._p_in2.high()
