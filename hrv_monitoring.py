from machine import ADC, Pin
import time
import math
from heartbeat_monitoring import HeartbeatMonitor
import uasyncio as asyncio

class HRV_Monitor:
    def __init__(self, monitor, collection_duration=30000):
        self.monitor = monitor
        self.collection_duration = collection_duration 
        self.intervals = [] 

    async def collect_data(self):
        self.intervals = []
        self.monitor.start()
        
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < self.collection_duration:
            self.monitor.process()
            if self.monitor.intervals:
                self.intervals.extend(self.monitor.intervals)
                self.monitor.intervals = []
            await asyncio.sleep_ms(5)
        
        self.monitor.stop()

    def calculate_mean_ppi(self):
        if not self.intervals:
            return 0
        return sum(self.intervals) / len(self.intervals)

    def calculate_mean_hr(self):
        mean_ppi = self.calculate_mean_ppi()
        if mean_ppi == 0:
            return 0
        return 60000 / mean_ppi

    def calculate_rmssd(self):
        if len(self.intervals) < 2:
            return 0 
        squared_diffs = [(self.intervals[i+1] - self.intervals[i])**2 for i in range(len(self.intervals)-1)]
        mean_squared_diffs = sum(squared_diffs) / len(squared_diffs)
        return math.sqrt(mean_squared_diffs)

    def calculate_sdnn(self):
        if not self.intervals:
            return 0
        mean_ppi = self.calculate_mean_ppi()
        squared_deviations = [(interval - mean_ppi)**2 for interval in self.intervals]
        mean_squared_deviations = sum(squared_deviations) / len(squared_deviations)
        return math.sqrt(mean_squared_deviations)

    async def calculate_all_metrics(self):
        await self.collect_data()
        
        metrics = {
            'MEAN_PPI_MS': self.calculate_mean_ppi(),
            'MEAN_HR_BPM': self.calculate_mean_hr(),
            'RMSSD_MS': self.calculate_rmssd(),
            'SDNN_MS': self.calculate_sdnn(),
            'INTERVAL_COUNT': len(self.intervals)
        }
        
        return metrics