from fifo import Fifo
from machine import Pin, I2C
import time

class Encoder:
    def __init__(self):
        self.a = Pin(10, mode=Pin.IN)
        self.b = Pin(11, mode=Pin.IN)
        self.push = Pin(12, Pin.IN, Pin.PULL_UP)
        self.sw0 = Pin(9, Pin.IN, Pin.PULL_UP)
        self.sw1 = Pin(8, Pin.IN, Pin.PULL_UP)
        self.sw2 = Pin(7, Pin.IN, Pin.PULL_UP)
        self.fifo = Fifo(30, typecode='i')
        self.debounce_ms = 150
        self.last_a_time = 0
        self.last_push_time = 0
        self.last_sw0_time = 0
        self.last_sw1_time = 0
        self.last_sw2_time = 0
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)
        self.push.irq(handler=self.push_handler, trigger=Pin.IRQ_FALLING, hard=True)
        self.sw0.irq(handler=self.sw0_handler, trigger=Pin.IRQ_FALLING, hard=True)
        self.sw1.irq(handler=self.sw1_handler, trigger=Pin.IRQ_FALLING, hard=True)
        self.sw2.irq(handler=self.sw2_handler, trigger=Pin.IRQ_FALLING, hard=True)

    """ Rotary Encoder Values : -1 and 1 = Rotation, 2 = Push """

    """SW0 = 3, SW1 = 4, SW2 = 5"""

    def handler(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_a_time) > self.debounce_ms:
            if self.b.value():
                self.fifo.put(-1)
            else:
                self.fifo.put(1)
            self.last_a_time = now

    def push_handler(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_push_time) > self.debounce_ms:
            self.fifo.put(2)
            self.last_push_time = now

    def sw0_handler(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_sw0_time) > self.debounce_ms:
            self.fifo.put(3)
            self.last_sw0_time = now

    def sw1_handler(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_sw1_time) > self.debounce_ms:
            self.fifo.put(4)
            self.last_sw1_time = now

    def sw2_handler(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_sw2_time) > self.debounce_ms:
            self.fifo.put(5)
            self.last_sw2_time = now
