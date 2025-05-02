import mip
import network
from time import sleep
from umqtt.simple import MQTTClient

SSID = "KMD652_Group_3"
PASSWORD = "BlendiFaiezeVeeti"
BROKER_IP = "192.168.3.253"
PORT = 1883


class Network:
    def __init__(self, ssid, password, broker_ip, client_id=""):
        self.ssid = ssid
        self.password = password
        self.broker_ip = broker_ip
        self.client_id = client_id
        self.wlan = network.WLAN(network.STA_IF)
        self.mqtt_client = None

    def connect_wifi(self):
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
        while not self.wlan.isconnected():
            print("Connecting to Wi-Fi...")
            sleep(1)
        print("Connected to Wi-Fi. IP:", self.wlan.ifconfig()[0])

    def install_mqtt_library(self):
        try:
            mip.install("umqtt.simple")
        except Exception as e:
            print(f"Could not install MQTT library: {e}")

    def connect_mqtt(self):
        self.mqtt_client = MQTTClient(self.client_id, self.broker_ip)
        self.mqtt_client.connect(clean_session=True)
        print("Connected to MQTT broker.")

    def send_message(self, topic, message):
        if self.mqtt_client:
            self.mqtt_client.publish(topic, message)
            print(f"Sending to MQTT: {topic} -> {message}")
        else:
            print("MQTT client not connected.")


network_system = Network(SSID, PASSWORD, BROKER_IP)
network_system.connect_wifi()
network_system.install_mqtt_library()

try:
    network_system.connect_mqtt()
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")
else:
    try:
        while True:
            network_system.send_message("test", "SLAYyyyy")
            sleep(5)
    except Exception as e:
        print(f"Failed to send MQTT message: {e}")
