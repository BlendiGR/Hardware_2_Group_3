from fifo import Fifo
import json
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

class History:
    def __init__(self, encoder):
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.oled_width = 128
        self.oled_height = 64
        self.oled = SSD1306_I2C(self.oled_width, self.oled_height, self.i2c)
        self.selected = 0
        self.enc = encoder
        self.history = None
        self.data_showing = False

    def invert_text(self, text, x, y, selected=False):
        if selected:
            rect_width = len(text) * 8
            self.oled.fill_rect(x, y - 1, rect_width, 9, 1)
            self.oled.text(text, x, y, 0)
        else:
            self.oled.text(text, x, y, 1)

    def append_metrics_to_history(self, metrics_data, time_stamp):
        if not metrics_data:
            return
        
        metrics = metrics_data.copy()
        metrics.append({"time": time_stamp})
        
        history_data = []
        try:
            with open("history.json", "r") as f:
                history_data = json.load(f)
        except:
            history_data = []
     
        history_data.append(metrics)
        
        with open("history.json", "w") as f:
            json.dump(history_data, f)

    def read_json(self):
        self.oled.fill(0)
        self.invert_text("HISTORY", 30, 0, True)
        with open("history.json", "r") as f:
            self.history = json.load(f)
            
        self.oled.show()

    def parse_menu(self):
        self.oled.fill(0)
        
        window_size = 3
        start = max(0, min(self.selected - 1, len(self.history) - window_size))
        end = min(start + window_size, len(self.history))

        self.invert_text("History", 30, 0, True)
        
        for display_xy, i in enumerate(range(start, end)):
            self.invert_text(f"{i+1}. Measurement", 1, (display_xy+2) * 10, i == self.selected)
        
        self.invert_text("BACK: SW0", 0, 56, True)
        self.oled.show()
        
    def show_data(self):
        self.oled.fill(0)
        
    
        metrics_list = self.history[self.selected]
        metrics = {}
        for item in metrics_list:
            metrics.update(item)
        
        time = metrics["time"][:10]
        
        self.invert_text(time, 20, 0, True)
        self.oled.text(f"HR: {metrics['HR']:.1f}", 4, 16, 1)
        self.oled.text(f"STRESS: {metrics['STRESS']}", 4, 24, 1)
        self.oled.text(f"RMSSD: {metrics['RMSSD']}", 4, 32, 1)
        self.oled.text(f"READNS: {metrics['READNS']}", 4, 40, 1)
        self.oled.text(f"PNS: {metrics['PNS']}", 4, 48, 1)
        self.oled.text(f"SNS: {metrics['SNS']}", 4, 56, 1)
        self.oled.show()

    def run(self):
        self.read_json()
        self.parse_menu()
        while True:
            while self.enc.fifo.has_data():
                fifo = self.enc.fifo.get()
                if fifo == -1:
                    if self.selected > 0:
                        self.selected -= 1
                        self.parse_menu()
                elif fifo == 1:
                    if self.selected < len(self.history) - 1:
                        self.selected += 1
                        self.parse_menu()
                elif fifo == 2:
                    if not self.data_showing:
                        self.show_data()
                        self.data_showing = True
                    else:
                        self.parse_menu()
                        self.data_showing = False
                elif fifo == 3:
                    return  # Exit method
