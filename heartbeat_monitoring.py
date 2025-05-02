from machine import ADC, Pin
from piotimer import Piotimer
from fifo import Fifo
import time

class ADC_Fifo(Fifo):
    def __init__(self, size, adc_pin):
        super().__init__(size)
        self.adc = ADC(Pin(adc_pin, Pin.IN))
    
    def handler(self, tid):
        self.put(self.adc.read_u16())

class HeartbeatMonitor:
    def __init__(self, adc_pin, sample_rate):
        self.fifo = ADC_Fifo(50, adc_pin)
        self.timer = None
        self.history = []
        self.smoothed_history = []
        self.last_beat_time = 0
        self.beat_detected = False
        self.intervals = []
        self.report_interval = 5000
        self.last_report_time = 0
        self.latest_bpm = 0
        self.smoothing_window = 15
        self.debounce_time = 300 
        self.is_running = False
        self.sample_rate = sample_rate
    
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.history = []
            self.smoothed_history = []
            self.intervals = []
            self.last_beat_time = 0
            self.beat_detected = False
            self.last_report_time = time.ticks_ms()
            self.timer = Piotimer(mode=Piotimer.PERIODIC, freq=self.sample_rate, callback=self.fifo.handler)
    
    def stop(self):
        if self.is_running:
            self.is_running = False
            self.timer.deinit()
            self.latest_bpm = 0
            self.intervals = []
    
    def get_bpm(self):
        return self.latest_bpm
    
    def process(self):
        if not self.is_running:
            return
        
        current_time = time.ticks_ms()
        while not self.fifo.empty():
            value = self.fifo.get()
            self.history.append(value)
            if len(self.history) > 250:
                self.history.pop(0)
            
            if len(self.history) >= self.smoothing_window:
                smoothed_value = sum(self.history[-self.smoothing_window:]) / self.smoothing_window
                self.smoothed_history.append(smoothed_value)
                if len(self.smoothed_history) > 250:
                    self.smoothed_history.pop(0)
                
                if len(self.smoothed_history) >= 250:
                    minimum = min(self.smoothed_history)
                    maximum = max(self.smoothed_history)
                    signal_range = maximum - minimum
                    threshold_on = minimum + 0.6 * signal_range
                    threshold_off = minimum + 0.4 * signal_range
                    
                    if not self.beat_detected and smoothed_value > threshold_on and time.ticks_diff(current_time, self.last_beat_time) >= self.debounce_time:
                        self.beat_detected = True
                        if self.last_beat_time != 0:
                            interval = time.ticks_diff(current_time, self.last_beat_time)
                            if 333 <= interval <= 1500:
                                self.intervals.append(interval)
                        self.last_beat_time = current_time
                    elif self.beat_detected and smoothed_value < threshold_off:
                        self.beat_detected = False
        
        if time.ticks_diff(current_time, self.last_report_time) >= self.report_interval:
            if self.intervals:
                avg_interval = sum(self.intervals) / len(self.intervals)
                bpm = round(60000 / avg_interval)
                self.latest_bpm = bpm if 40 <= bpm <= 180 else 0
            else:
                self.latest_bpm = 0
            self.intervals = []
            self.last_report_time = current_time
