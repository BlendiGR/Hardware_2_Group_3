from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

import json
import time
import uasyncio as asyncio

class UI:
    def __init__(self, options, selected, bpm, hrv_calculator=None):
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.oled_width = 128
        self.oled_height = 64
        self.oled = SSD1306_I2C(self.oled_width, self.oled_height, self.i2c)
        
        self.options = options
        self.selected = selected
        self.bpm = bpm 
        self.hrv_calculator = hrv_calculator
        
        self.latest_time = None

    def invert_text(self, text, x, y, selected=False):
        if selected:
            rect_width = len(text) * 8
            self.oled.fill_rect(x, y - 1, rect_width, 9, 1)
            self.oled.text(text, x, y, 0)
        else:
            self.oled.text(text, x, y, 1)

    def main_menu(self):
        self.oled.fill(0)
        for option in range(len(self.options)):
            self.invert_text(self.options[option], 1, (option + 1) * 10, option == self.selected)
        self.oled.show()
        
    def draw_ppg(self, data, bpm):

        if len(data) < 120:
            self.oled.fill(0)
            self.oled.text("HOLD FINGER", 18, 16, 1)
            self.oled.text("ON SENSOR", 24, 24, 1)
            self. invert_text("PRESS TO EXIT", 8, 50, True)
            self.oled.show()
            return False


        data_window = data[-120:]

        min_val = min(data_window)
        max_val = max(data_window)

        self.oled.fill(0)
        for i in range(len(data_window) - 1):
            y1 = 53 - int((data_window[i] - min_val) / (max_val - min_val) * 50)
            x1 = i
            y2 = 53 - int((data_window[i + 1] - min_val) / (max_val - min_val) * 50)
            x2 = i + 1
            self.oled.line(x1, y1, x2, y2, 1)

        bpm_text = f"{bpm} BPM" if 30 <= bpm <= 200 else "-- BPM"
        self.invert_text(bpm_text, 60, 55, True)

        self.oled.show()
        return True

    def hrv_menu(self):
        self.oled.fill(0)
        self.oled.text("PLACE FINGER", 18, 16, 1)
        self.oled.text("ON SENSOR", 30, 24, 1)
        self.invert_text("PRESS TO START", 10, 40, True)
        self.oled.show()
        
    def hrv_measuring(self):
        self.oled.fill(0)
        self.oled.text("Calculating...", 4, 42, 1)
        self.oled.show()

    def display_hrv_metrics(self, metrics):
        self.oled.fill(0)
        self.oled.text("HRV RESULTS", 20, 0, 1)
        self.oled.text(f"HR: {metrics['MEAN_HR_BPM']:.1f} BPM", 4, 12, 1)
        self.oled.text(f"PPI: {metrics['MEAN_PPI_MS']:.1f} ms", 4, 22, 1)
        self.oled.text(f"RMSSD: {metrics['RMSSD_MS']:.1f} ms", 4, 32, 1)
        self.oled.text(f"SDNN: {metrics['SDNN_MS']:.1f} ms", 4, 42, 1)
        self.invert_text("PRESS TO EXIT", 10, 53, True)
        self.oled.show()
        
    async def loading_bar(self, seconds):
        self.oled.fill(0)
        self.oled.text("MEASURING..", 4, 10, 1)
        bar_x, bar_y = 4, 30
        bar_width, bar_height = 120, 10
        self.oled.rect(bar_x, bar_y, bar_width, bar_height, 1)
        start_time = time.ticks_ms()
        duration_ms = seconds * 1000
        while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
            progress = time.ticks_diff(time.ticks_ms(), start_time) / duration_ms
            fill_width = int(bar_width * progress)
            self.oled.fill_rect(bar_x, bar_y, fill_width, bar_height, 1)
            self.oled.show()
            await asyncio.sleep_ms(50)
        self.oled.fill_rect(bar_x, bar_y, bar_width, bar_height, 1)
        self.oled.show()
        
    def kubios_extract(self, json):
        sorted_metrics = []
        
        # Decode MQTT byte string and parse JSON
        health_metrics = json
        
        # Extract metrics from nested JSON structure
        metrics = health_metrics["data"]["analysis"]
        stress = metrics["stress_index"]
        readiness = metrics["readiness"]
        heart_rate = metrics["mean_hr_bpm"]
        rmssd = metrics["rmssd_ms"]
        pns_index = metrics["pns_index"]
        sns_index = metrics["sns_index"]
        time_stamp = metrics["create_timestamp"]
        
        self.latest_time = time_stamp
        
        # Append heart rate (BPM)
        sorted_metrics.append({"HR": heart_rate})
        
        # Categorize Stress Index
        if stress < 7:
            sorted_metrics.append({"STRESS": "LOW"})
        elif 7 <= stress <= 12:
            sorted_metrics.append({"STRESS": "NORM"})
        else:
            sorted_metrics.append({"STRESS": "HIGH"})
        
        # Categorize RMSSD
        if rmssd < 20:
            sorted_metrics.append({"RMSSD": "LOW"})
        elif 20 <= rmssd <= 50:
            sorted_metrics.append({"RMSSD": "NORM"})
        else:
            sorted_metrics.append({"RMSSD": "HIGH"})
        
        # Categorize Readiness
        if readiness < 50:
            sorted_metrics.append({"READNS": "LOW"})
        elif 50 <= readiness <= 70:
            sorted_metrics.append({"READNS": "NORM"})
        else:
            sorted_metrics.append({"READNS": "HIGH"})
        
        # Categorize PNS Index
        if pns_index < -1:
            sorted_metrics.append({"PNS": "LOW"})
        elif -1 <= pns_index <= 1:
            sorted_metrics.append({"PNS": "NORM"})
        else:
            sorted_metrics.append({"PNS": "HIGH"})
        
        # Categorize SNS Index
        if sns_index < -1:
            sorted_metrics.append({"SNS": "LOW"})
        elif -1 <= sns_index <= 1:
            sorted_metrics.append({"SNS": "NORM"})
        else:
            sorted_metrics.append({"SNS": "HIGH"})
        
        return sorted_metrics
    
    
    def display_kubios(self, metrics):
        self.oled.fill(0)
        self.invert_text("RESULTS KUBIOS", 8, 0, True)
        y = 9
        row = 1
        
        sorted_metrics = metrics
        
        for metric_dict in sorted_metrics:
            key, value = list(metric_dict.items())[0]
            if key == "HR":
                text = f"{key}: {value:.1f} BPM"
            else:
                text = f"{key}: {value}"
            self.oled.text(text, 4, y * row, 1)
            row += 1
            
        self.oled.show()


            
            
            
    
    
