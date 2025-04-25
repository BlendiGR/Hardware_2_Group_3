from fifo import Fifo
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from controls import Encoder
from heartbeat_monitoring import Heartbeat_Monitor as hbmon
import time

class MainMenu:
    def __init__(self):

        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.oled_width = 128
        self.oled_height = 64
        self.oled = SSD1306_I2C(self.oled_width, self.oled_height, self.i2c)

        self.running = False
        self.monitor = hbmon()
        self.enc = Encoder()
        self.last_display_time = 0
        
        self.oled.fill(0)
        self.oled.show()

    def draw_options(self):
        """Draw the menu based on running state."""
        self.oled.fill(0)
        
        if self.running:
            bpm = self.monitor.get_bpm()
            self.oled.text(f"BPM: {bpm}", 40, 16)
            self.oled.text("Press to stop", 20, 32)
        else:
            self.oled.text("Press to start", 20, 16)
            self.oled.text("measurement", 28, 32)
        
        self.oled.show()

    def run(self):
        """Main loop to handle encoder input and update display."""
        self.draw_options()
        while True:
            while self.enc.fifo.has_data():
                fifo = self.enc.fifo.get()
                if fifo == 2:
                    self.running = not self.running
                    if self.running:
                        self.monitor.start()
                    else:
                        self.monitor.stop()
                    self.draw_options()

            self.monitor.run()

            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, self.last_display_time) >= 100:
                self.draw_options()
                self.last_display_time = current_time

            time.sleep(0.005)
            
menu = MainMenu()

menu.run()