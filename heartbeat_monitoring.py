import asyncio
from machine import ADC, Pin
import time

class Heartbeat_Monitor:
    def __init__(self):
        self.adc = ADC(Pin(26, Pin.IN))
        self.history = [] 
        self.history_size = 250
        self.smoothed_history = []
        self.last_beat_time = 0 
        self.beat_detected = False 
        self.threshold_on = 0 
        self.threshold_off = 0 
        self.intervals = [] 
        self.report_interval = 5000
        self.last_report_time = 0  
        self.is_running = False  
        self.latest_bpm = 0

    def moving_average(self, data, window=5):
        if not data:
            return 0
        if len(data) < window:
            return sum(data) / len(data)
        return sum(data[-window:]) / window

    def start(self):
        self.is_running = True
        self.history = []
        self.smoothed_history = []
        self.intervals = []
        self.last_beat_time = 0
        self.beat_detected = False
        self.last_report_time = time.ticks_ms()

    def stop(self):
        self.is_running = False
        self.latest_bpm = 0
        self.intervals = []

    def get_bpm(self):
        return self.latest_bpm

    def run(self):
        if not self.is_running:
            return
        

        value = self.adc.read_u16()
        self.history.append(value)
        self.history = self.history[-self.history_size:]


        smoothed_value = self.moving_average(self.history)
        self.smoothed_history.append(smoothed_value)
        self.smoothed_history = self.smoothed_history[-self.history_size:]


        if len(self.history) < self.history_size:
            time.sleep(0.005)
            return

        minimum, maximum = min(self.smoothed_history), max(self.smoothed_history)
        self.threshold_on = (minimum + 2 * maximum) // 3
        self.threshold_off = (minimum + maximum) // 2

        current_time = time.ticks_ms()
        if not self.beat_detected and smoothed_value > self.threshold_on:
            self.beat_detected = True
            print("Heartbeat detected")
            if self.last_beat_time != 0:
                interval = time.ticks_diff(current_time, self.last_beat_time)
                if 333 <= interval <= 1500:
                    self.intervals.append(interval)
            self.last_beat_time = current_time
        elif self.beat_detected and smoothed_value < self.threshold_off:
            self.beat_detected = False

        if time.ticks_diff(current_time, self.last_report_time) >= self.report_interval:
            if self.intervals:
                avg_interval = sum(self.intervals) / len(self.intervals)
                bpm = 60000 // avg_interval
                if 40 <= bpm <= 180:
                    self.latest_bpm = bpm
                else:
                    self.latest_bpm = 0
            else:
                self.latest_bpm = 0
            
            self.intervals = []
            self.last_report_time = current_time

        time.sleep(0.005)