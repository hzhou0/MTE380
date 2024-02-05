# tcs3200.py: a driver for the TCS3200 color sensor
#
# Copyright (c) U. Raich
# Written for the course on the Internet of Things at the
# University of Cape Coast, Ghana
# The program is released under the MIT licence
import rp2
from machine import Pin, freq


class TCS3200(object):
    """
    This class reads RGB values from a TCS3200 colour sensor.

    GND   Ground.
    VDD   Supply Voltage (2.7-5.5V)
    LED   1: LEDs on, 0: LEDs off
    /OE   Output enable, active low. When OE is high OUT is disabled
         allowing multiple sensors to share the same OUT line.
    OUT   Output frequency square wave.
    S0/S1 Output frequency scale selection.
    S2/S3 Colour filter selection.

    OUT is a square wave whose frequency is proportional to the
    intensity of the selected filter colour.
    """

    # S2, S3 control color filter
    RED = (0, 0)
    BLUE = (0, 1)
    GREEN = (1, 1)
    CLEAR = (1, 0)
    # S0, S1 control frequency scaling on output pin
    FREQ_12_KHZ = (0, 1)
    FREQ_120_KHZ = (1, 0)
    FREQ_600_KHZ = (1, 1)

    # _REL_COMP = (161212, 168096, 233470)
    REL_COMP = (1, 0.959047211, 0.690504133)

    def __init__(
        self,
        state_machine_id: int,
        out: int,
        s2: int,
        s3: int,
        s0: int = None,
        s1: int = None,
        led: int = None,
        oe: int = None,
    ):
        """
        The GPIOs connected to the sensor OUT, S2, and S3 pins must
        be specified.  The S0, S1 (frequency) and LED and OE (output enable)
        GPIOs are optional.
        The OE pin is missing on some TCS3200 boards
        """
        self._out = Pin(out, Pin.IN, Pin.PULL_UP)

        self._s2 = Pin(s2, Pin.OUT)
        self._s3 = Pin(s3, Pin.OUT)
        self._s0 = Pin(s0, Pin.OUT) if s0 else None
        self._s1 = Pin(s1, Pin.OUT) if s1 else None
        if self._s0 and self._s1:
            self.max_freq = self.FREQ_600_KHZ
        self._oe = Pin(oe, Pin.OUT) if oe else None
        self.led = Pin(led, Pin.OUT) if led else None

        # noinspection PyUnresolvedReferences,PyArgumentList
        @rp2.asm_pio()
        def wave_duration():
            pull()
            # initialize scratch reg x to 0x1111
            mov(x, invert(null))
            set(y, 31)

            label("WAVE_START")
            # wait on base pin to become high
            wait(1, pin, 0)
            # wait on base pin to become low (start of the square wave)
            wait(0, pin, 0)

            label("LOOP")
            # if base pin to become high (end of wave), goto return
            jmp(pin, "RETURN")
            # else decrement reg x
            jmp(x_dec, "LOOP")

            label("RETURN")
            jmp(y_dec, "WAVE_START")
            # Move x value into ISR.
            # The x value is the duration of the square wave in clock cycles (unsigned complement).
            mov(isr, invert(x))
            # Push into FIFO RX
            push()

        self._sm = rp2.StateMachine(
            state_machine_id,
            wave_duration,
            freq=freq(),
            in_base=self._out,
            jmp_pin=self._out,
        )
        self._sm.active(1)

    # sets the filters
    @property
    def filter(self) -> tuple[int, int]:
        return self._s2.value(), self._s3.value()

    @filter.setter
    def filter(self, x: tuple[int, int]):
        self._s2.value(x[0])
        self._s3.value(x[1])

    @property
    def max_freq(self) -> tuple[int, int]:
        if not self._s0 or not self._s1:
            raise RuntimeError("s0 or s1 not provided, unknown max freq")
        return self._s0.value(), self._s1.value()

    @max_freq.setter
    def max_freq(self, x: tuple[int, int]):
        if not self._s0 or not self._s1:
            raise RuntimeError("s0 or s1 not provided, not able to set max freq")
        self._s0.value(x[0])
        self._s1.value(x[1])

    @micropython.native
    def freq(self, filter: tuple[int, int]) -> int:
        self.filter = filter
        self._sm.put(0)
        return int(freq() / (self._sm.get() / 32))

    @micropython.native
    def rgb(self) -> tuple[int, int, int]:
        rgb_raw = self.rgb_raw()

        return tuple(
            int(v * 255 * self.REL_COMP[i] / max(rgb_raw))
            for i, v in enumerate(rgb_raw)
        )

    @micropython.native
    def rgb_raw(self) -> tuple[int, int, int]:
        return (
            self.freq(self.RED),
            self.freq(self.GREEN),
            self.freq(self.BLUE),
        )
