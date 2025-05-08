import mip
import network
import json
import urequests as requests
import time
from umqtt.simple import MQTTClient
import random

class Network:
    def __init__(self, ssid, password, broker_ip, client_id=""):
        self.ssid = ssid
        self.password = password
        self.broker_ip = broker_ip
        self.client_id = client_id
        self.wlan = network.WLAN(network.STA_IF)
        self.mqtt_client = None
        self.last_message = None

    def connect_wifi(self):
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
        while not self.wlan.isconnected():
            print("Connecting to Wi-Fi...")
            time.sleep(1)
        print("Connected to Wi-Fi. IP:", self.wlan.ifconfig()[0])

    def install_mqtt_library(self):
        mip.install("umqtt.simple")

    def connect_mqtt(self, port=21883):
        self.mqtt_client = MQTTClient(self.client_id, self.broker_ip, port=port)
        self.mqtt_client.set_callback(self._mqtt_callback)
        self.mqtt_client.connect(clean_session=True)
        print(f"Connected to MQTT broker on port {port}.")

    def _mqtt_callback(self, topic, msg):
        print(f"Received MQTT message on topic {topic}: {msg}")
        self.last_message = json.loads(msg.decode('utf-8'))


    def send_kubios(self, id, data, response_topic="kubios-response", timeout=10):
        raw_data = {
            "id": str(id),
            "type": "RRI",
            "data": data,
            "analysis": {"type": "readiness"}
        }
        json_data = json.dumps(raw_data).encode("utf-8")
        
        if not self.mqtt_client:
            print("MQTT client not connected.")
            return None

        self.last_message = None
        self.mqtt_client.subscribe(response_topic.encode('utf-8'))
        print(f"Subscribed to response topic: {response_topic}")

        request_topic = "kubios-request"
        self.mqtt_client.publish(request_topic.encode('utf-8'), json_data)
        print(f"Sending to MQTT: {request_topic} -> {json_data}")

        start_time = time.ticks_ms()
        while time.ticks_ms() - start_time < timeout * 1000:
            self.mqtt_client.check_msg()
            if self.last_message is not None:
                return self.last_message
            time.sleep(0.1)

        print("Timeout waiting for Kubios response.")
        return None
    
    def send_hrv_data(self, metrics, topic):
        
        self.mqtt_client.subscribe(topic.encode('utf-8'))
        
        data ={
            "id": time.time(),
            "timestamp": random.randint(1, 1000),
            "mean_hr": metrics["MEAN_HR_BPM"],
            "mean_ppi": metrics["MEAN_PPI_MS"],
            "rmssd": metrics["RMSSD_MS"],
            "sdnn": metrics["SDNN_MS"],
            }
        
        
        message_json = json.dumps(data)
        if self.mqtt_client:
            self.mqtt_client.publish(topic, message_json)
            print(f"Sending to MQTT: {topic} -> {message_json}")
        else:
            print("MQTT client not connected.")

    def send_kubios_data(self, health_metrics, topic):
        self.mqtt_client.subscribe(topic.encode('utf-8'))
        metrics = health_metrics["data"]["analysis"]
        
        data = {
            "id": round(time.time()),
            "timestamp": random.randint(1, 1000),
            "mean_hr": metrics["mean_hr_bpm"],
            "mean_ppi": metrics["mean_rr_ms"],
            "rmssd": metrics["rmssd_ms"],
            "sdnn": metrics["sdnn_ms"],
            "sns": metrics["sns_index"],
            "pns": metrics["pns_index"],
        }
        
        message_json = json.dumps(data)
        if self.mqtt_client:
            self.mqtt_client.publish(topic, message_json)
            print(f"Sending to MQTT: {topic} -> {message_json}")
        else:
            print("MQTT client not connected.")
