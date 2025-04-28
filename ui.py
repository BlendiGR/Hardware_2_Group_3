from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
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
        self.bpm = bpm  # Kept for compatibility, but not used in draw_ppg
        self.hrv_calculator = hrv_calculator

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
        self.oled.text("ON SENSOR", 10, 24, 1)
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
        self.oled.text("Calculating HRV..", 4, 10, 1)
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