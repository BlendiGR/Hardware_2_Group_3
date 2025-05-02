from fifo import Fifo
from controls import Encoder
from heartbeat_monitoring import HeartbeatMonitor
from networker import Network
from ui import UI
from hrv_monitoring import HRV_Monitor
from history import History
import uasyncio as asyncio
import time

class MainMenu:
    def __init__(self):
        self.running = False
        self.monitor = HeartbeatMonitor(26, 200)
        self.hrv_monitor = HRV_Monitor(self.monitor)
        self.enc = Encoder()
        self.history = History(self.enc)
        self.network = Network("KMD652_Group_3", "BlendiFaiezeBlendi", "192.168.3.253")
        
        self.last_display_time = 0
        self.last_ppg_time = 0
        self.options = ["HEARTRATE", "HRV ANALYSIS", "ADVANCED HRV", "HISTORY"]

        self.selected = 0
        self.current_menu = "main"
        self.intervals = self.hrv_monitor.intervals
        
        self.ui = UI(self.options, self.selected, self.monitor.get_bpm())
        self.hrv_metrics = None
        self.id = 0
        
        self.history_selected = 0

    def draw_options(self):
        self.ui.selected = self.selected
        self.ui.bpm = self.monitor.get_bpm()
        if self.current_menu == "main":
            self.ui.main_menu()
        elif self.current_menu == "hrv":
            self.ui.hrv_menu()
        elif self.current_menu == "measuring_hrv":
            self.ui.hrv_measuring()
        elif self.current_menu == "kubios":
            self.ui.hrv_menu()
            
            

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
                        elif self.selected == 2:
                            self.current_menu = "kubios"
                            self.draw_options()
                        elif self.selected == 3:
                            self.history.run()
                            
                    elif self.current_menu == "hrv":
                        self.network.connect_mqtt()
                        self.current_menu = "measuring_hrv"
                        self.draw_options()
                        results = await asyncio.gather(
                            self.ui.loading_bar(30),
                            self.hrv_monitor.calculate_all_metrics()
                        )
                        self.hrv_metrics = results[1]
                        self.network.send_message("hrv/metrics", self.hrv_metrics)
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
                        
                    elif self.current_menu == "kubios":
                        self.network.connect_mqtt(21883)
                        results = await asyncio.gather(
                            self.ui.loading_bar(30),
                            self.hrv_monitor.collect_data()
                        )
                        self.id +=1
                        self.intervals = self.hrv_monitor.intervals
                        kubios_response = self.network.send_kubios(self.id, self.intervals)
                        kubios_extracted = self.ui.kubios_extract(kubios_response)
                        self.history.append_metrics_to_history(kubios_extracted, self.ui.latest_time)
        
                        
                        while True:
                            self.ui.display_kubios(kubios_extracted)
                            if self.enc.fifo.has_data():
                                fifo = self.enc.fifo.get()
                                if fifo == 2:
                                    break
                            await asyncio.sleep(0.1)
                        self.current_menu = "main"
                        self.draw_options()
                        
            if self.current_menu == "heart_rate" and self.running:
                self.monitor.process()
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