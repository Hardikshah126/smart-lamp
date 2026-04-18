import json
import time
import paho.mqtt.client as mqtt

BROKER_HOST = "broker.hivemq.com"
BROKER_PORT = 1883
CLIENT_ID   = "smart-lamp-python-edge"

TOPIC_EMOTION    = "smartlamp/emotion"
TOPIC_MODE       = "smartlamp/mode"
TOPIC_SENSOR_LDR = "smartlamp/sensor/ldr"
TOPIC_SENSOR_PIR = "smartlamp/sensor/pir"
TOPIC_SENSOR_DHT = "smartlamp/sensor/dht"
TOPIC_ENERGY     = "smartlamp/energy"
TOPIC_ALERT      = "smartlamp/alert"


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client(client_id=CLIENT_ID)

        self.client.on_connect    = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message    = self._on_message

        self.connected = False

        # 🔥 REAL SENSOR VALUES
        self.ldr_value   = None
        self.pir_value   = None
        self.temperature = None
        self.humidity    = None
        self.energy_kwh  = None

    def connect(self):
        print(f"[MQTT] Connecting to {BROKER_HOST}:{BROKER_PORT}...")
        self.client.connect(BROKER_HOST, BROKER_PORT, 60)
        self.client.loop_start()

        while not self.connected:
            time.sleep(0.1)

        print("[MQTT] Connected.")

    def publish_emotion(self, emotion, mode):
        payload = json.dumps({"emotion": emotion, "mode": mode})
        self.client.publish(TOPIC_EMOTION, payload)
        self.client.publish(TOPIC_MODE, mode)
        print(f"[MQTT] Published → emotion={emotion}, mode={mode}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            for topic in [
                TOPIC_SENSOR_LDR,
                TOPIC_SENSOR_PIR,
                TOPIC_SENSOR_DHT,
                TOPIC_ENERGY,
                TOPIC_ALERT
            ]:
                client.subscribe(topic)
                print(f"[MQTT] Subscribed to {topic}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("[MQTT] Disconnected")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        try:
            if topic == TOPIC_SENSOR_LDR:
                self.ldr_value = float(payload)

            elif topic == TOPIC_SENSOR_PIR:
                self.pir_value = int(payload)

            elif topic == TOPIC_SENSOR_DHT:
                data = json.loads(payload)
                self.temperature = data.get("temp")
                self.humidity = data.get("humidity")

            elif topic == TOPIC_ENERGY:
                self.energy_kwh = float(payload)

            elif topic == TOPIC_ALERT:
                print(f"[ALERT] {payload}")

        except Exception as e:
            print("MQTT Parse Error:", e)