import time
from machine import Pin

from tcs3200 import TCS3200

print("hello world")
led = Pin(25, Pin.OUT)
tcs3200 = TCS3200(OUT=20, S3=21, S2=22, S1=26, S0=27, OE=28)
tcs3200.freq_divider = tcs3200.TWO_PERCENT
print(tcs3200.freq_divider)
if tcs3200.freq_divider == tcs3200.TWO_PERCENT:
    print("Frequency divider is set to 2%")
else:
    print("Something went wrong when setting the frequency divider")

# Set no of cycles to be measured
tcs3200.cycles = 100
tcs3200.calibrate()
while True:
    print(tcs3200.rgb)
    time.sleep_ms(100)
