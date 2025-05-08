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
        self.network = Network("KMD652_Group_3", "BlendiFaiezeVeeti", "192.168.3.253")
        self.options = ["HEARTRATE", "HRV ANALYSIS", "ADVANCED HRV", "HISTORY"]
        self.selected = 0
        self.current_menu = "main"
        self.ui = UI(self.options, self.selected, self.monitor.get_bpm())
        self.last_display_time = 0 #### VARIABLE FOR SHOWING REALTIME PPG AND HR
        self.last_ppg_time = 0 #### THIS IS ALSO A VARIABLE FOR THE REALTIME PPG
        self.hrv_metrics = None #### METRICS AFTER MEASURING HRV TO BE SHOWN ON THE SCREEN
        self.intervals = self.hrv_monitor.intervals #### INTERVALS TO BE SENT TO KUBIOS 
        self.id = 0  #### THIS IS THE ID WHEN SENDING KUBIOS REQUESTS
        self.kubios_extracted = None #### THE CLEAN DATA FROM KUBIOS TO BE SHOWN ON THE DISPLAY

    def handle_input(self, fifo):
        """  HANDLE ENCODER INPUT BASED ON CURRENT MENU   """
        if self.current_menu == "main":
            if fifo == 1 and self.selected < len(self.options) - 1:
                self.selected += 1
            elif fifo == -1 and self.selected > 0:
                self.selected -= 1
            elif fifo == 2:
                if self.selected == 0:
                    self.running = True
                    self.monitor.start()
                    self.current_menu = "heart_rate"
                elif self.selected == 1:
                    self.current_menu = "hrv"
                elif self.selected == 2:
                    self.current_menu = "kubios_menu"
                elif self.selected == 3:
                    self.history.run()
        elif self.current_menu == "heart_rate":
            if fifo == 2:
                self.running = False
                self.monitor.stop()
                self.current_menu = "main"
        elif self.current_menu == "hrv":
            if fifo == 2:
                self.current_menu = "measuring_hrv"
        elif self.current_menu == "kubios_menu":
            if fifo == 2:
                self.current_menu = "kubios_measure"
        elif self.current_menu == "hrv_results" or self.current_menu == "kubios_results":
            if fifo == 2:
                self.current_menu = "main"

    def update_ui(self):
        """  UPDATE THE UI BASED ON MENU STATE  """
        self.ui.selected = self.selected
        self.ui.bpm = self.monitor.get_bpm()
        if self.current_menu == "main":
            self.ui.main_menu()
        elif self.current_menu == "hrv":
            self.ui.hrv_menu()
        elif self.current_menu == "heart_rate":
            bpm = self.monitor.get_bpm()
            self.ui.draw_ppg(self.monitor.smoothed_history, bpm)
        elif self.current_menu == "hrv_results":
            self.ui.display_hrv_metrics(self.hrv_metrics)
        elif self.current_menu == "kubios_results":
            self.ui.display_kubios(self.kubios_extracted)
        elif self.current_menu == "kubios_menu":
            self.ui.hrv_menu()
 
    async def run(self):
        """   MAIN LOOP  """
        self.network.connect_wifi()
        self.update_ui()
        while True:
            # Process encoder input
            while self.enc.fifo.has_data():
                fifo = self.enc.fifo.get()
                self.handle_input(fifo)
                                                  ##### HANDLE BASIC HRV MEASUREMENT ####
                if self.current_menu == "measuring_hrv":
                    try:
                        self.network.connect_mqtt()
                        results = await asyncio.gather(
                            self.ui.loading_bar(30),
                            self.hrv_monitor.calculate_all_metrics()
                        )
                        self.hrv_metrics = results[1]
                        self.network.send_message("hrv/metrics", self.hrv_metrics)
                        self.current_menu = "hrv_results"
                    except Exception as e:
                        print(f"HRV measurement failed: {e}")
                        self.current_menu = "main"
                                                    ##### HANDLE KUBIOS ADVANCED HRV #####
                elif self.current_menu == "kubios_measure":
                    try:
                        self.network.connect_mqtt(21883)
                        results = await asyncio.gather(
                            self.ui.loading_bar(30),
                            self.hrv_monitor.collect_data()
                        )
                        self.id += 1
                        self.intervals = self.hrv_monitor.intervals
                        kubios_response = self.network.send_kubios(self.id, self.intervals)
                        self.kubios_extracted = self.ui.kubios_extract(kubios_response)
                        self.history.append_metrics_to_history(self.kubios_extracted, self.ui.latest_time)
                        self.current_menu = "kubios_results"
                    except Exception as e:
                        print(f"Kubios processing failed: {e}")
                        self.current_menu = "main"

            #### UPDATE THE PPG AND HEARTRATE ####
            current_time = time.ticks_ms()
            if self.current_menu == "heart_rate" and self.running:
                if time.ticks_diff(current_time, self.last_ppg_time) >= 50:
                    self.monitor.process()
                    self.update_ui()
                    self.last_ppg_time = current_time
            else:
                if time.ticks_diff(current_time, self.last_display_time) >= 100:
                    self.update_ui()
                    self.last_display_time = current_time

            await asyncio.sleep_ms(5)

if __name__ == "__main__":
    menu = MainMenu()
    asyncio.run(menu.run())
