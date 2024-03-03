import time
from machine import Pin, freq

from aio_tcs3200 import TCS3200

print("hello world")
freq(240000000)
print(freq())
led = Pin(25, Pin.OUT)
tcs3200 = TCS3200(state_machine_id=0, out=20, s3=21, s2=22, s1=26, s0=27, oe=28)
tcs3200.rgb_raw()
ms = 0
while True:
    val = tcs3200.rgb_lpf()
    if ms >= 1000:
        print(val)
        ms = 0
    else:
        ms += 1
