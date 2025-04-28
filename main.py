from fifo import Fifo
from controls import Encoder
from heartbeat_monitoring import Heartbeat_Monitor as hbmon
from ui import UI
from hrv_monitoring import HRV_Monitor
import uasyncio as asyncio
import time

class MainMenu:
    def __init__(self):
        self.running = False
        self.monitor = hbmon()
        self.hrv_monitor = HRV_Monitor(self.monitor)
        self.enc = Encoder()
        self.last_display_time = 0
        self.last_ppg_time = 0
        self.options = ["HEARTRATE", "HRV ANALYSIS"]
        self.selected = 0
        self.current_menu = "main"
        
        self.ui = UI(self.options, self.selected, self.monitor.get_bpm())
        self.hrv_metrics = None

    def draw_options(self):
        self.ui.selected = self.selected
        self.ui.bpm = self.monitor.get_bpm()
        if self.current_menu == "main":
            self.ui.main_menu()
        elif self.current_menu == "hrv":
            self.ui.hrv_menu()
        elif self.current_menu == "measuring_hrv":
            self.ui.hrv_measuring()

    async def run(self):
        self.draw_options()
        while True:
            while self.enc.fifo.has_data():
                fifo = self.enc.fifo.get()
                if fifo == 1 and self.selected < len(self.options) - 1 and self.current_menu == "main":
                    self.selected += 1
                    self.draw_options()
                elif fifo == -1 and self.selected > 0 and self.current_menu == "main":
                    self.selected -= 1
                    self.draw_options()
                elif fifo == 2:
                    if self.current_menu == "main":
                        if self.selected == 0:
                            self.running = True
                            self.monitor.start()
                            self.current_menu = "heart_rate"
                        elif self.selected == 1:
                            self.current_menu = "hrv"
                            self.draw_options()
                    elif self.current_menu == "hrv":
                        self.current_menu = "measuring_hrv"
                        self.draw_options()
                        results = await asyncio.gather(
                            self.ui.loading_bar(30),
                            self.hrv_monitor.calculate_all_metrics()
                        )
                        self.hrv_metrics = results[1]
                        while True:
                            self.ui.display_hrv_metrics(self.hrv_metrics)
                            if self.enc.fifo.has_data():
                                fifo = self.enc.fifo.get()
                                if fifo == 2:
                                    break
                            await asyncio.sleep(0.1)
                        self.current_menu = "main"
                        self.draw_options()
                    elif self.current_menu == "heart_rate":
                        self.running = False
                        self.monitor.stop()
                        self.current_menu = "main"
                        self.draw_options()
                        
            if self.current_menu == "heart_rate" and self.running:
                self.monitor.run()
                current_time = time.ticks_ms()
                if time.ticks_diff(current_time, self.last_ppg_time) >= 50:
                    bpm = self.monitor.get_bpm()
                    self.ui.draw_ppg(self.monitor.smoothed_history, bpm)
                    self.last_ppg_time = current_time

            if self.current_menu != "heart_rate":
                current_time = time.ticks_ms()
                if time.ticks_diff(current_time, self.last_display_time) >= 100:
                    self.draw_options()
                    self.last_display_time = current_time

            await asyncio.sleep_ms(5)

if __name__ == "__main__":
    menu = MainMenu()
    asyncio.run(menu.run())