"""
mqtt_client.py
Publishes emotion results and receives sensor data from ESP32 via MQTT.
Your teammate's ESP32 subscribes to the same broker.
Run: python mqtt_client.py (for testing)
"""

import json
import time
import threading
import paho.mqtt.client as mqtt

# ─── Config ───────────────────────────────────────────────────────────────────
# Use a free public broker for testing, switch to private for production
BROKER_HOST = "broker.hivemq.com"   # free public MQTT broker
BROKER_PORT = 1883
CLIENT_ID   = "smart-lamp-python-edge"

# Topics (share these exact strings with your teammate for ESP32 code)
TOPIC_EMOTION    = "smartlamp/emotion"       # Python → ESP32
TOPIC_MODE       = "smartlamp/mode"          # Python → ESP32
TOPIC_SENSOR_LDR = "smartlamp/sensor/ldr"   # ESP32 → Python
TOPIC_SENSOR_PIR = "smartlamp/sensor/pir"   # ESP32 → Python
TOPIC_SENSOR_DHT = "smartlamp/sensor/dht"   # ESP32 → Python
TOPIC_ENERGY     = "smartlamp/energy"        # ESP32 → Python
TOPIC_ALERT      = "smartlamp/alert"         # ESP32 → Python (temp emergency)


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
        self.client.on_connect    = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message    = self._on_message
        self.connected = False

        # Latest sensor values (updated by callbacks)
        self.ldr_value   = None
        self.pir_value   = None
        self.temperature = None
        self.humidity    = None
        self.energy_kwh  = None

        # External callbacks (set by cloud pusher or dashboard)
        self.on_sensor_update = None   # called with dict of sensor data
        self.on_alert         = None   # called with alert message string

    # ── Connection ────────────────────────────────────────────────────────────
    def connect(self, timeout: int = 10):
        print(f"[MQTT] Connecting to {BROKER_HOST}:{BROKER_PORT}...")
        self.client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        self.client.loop_start()

        # Wait for connection
        deadline = time.time() + timeout
        while not self.connected and time.time() < deadline:
            time.sleep(0.1)

        if not self.connected:
            raise ConnectionError(f"[MQTT] Could not connect to {BROKER_HOST} within {timeout}s")
        print("[MQTT] Connected.")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("[MQTT] Disconnected.")

    # ── Publish ───────────────────────────────────────────────────────────────
    def publish_emotion(self, emotion: str, mode: str):
        """Send detected emotion and lighting mode to ESP32."""
        payload = json.dumps({"emotion": emotion, "mode": mode, "ts": int(time.time())})
        self.client.publish(TOPIC_EMOTION, payload, qos=1)
        self.client.publish(TOPIC_MODE, mode, qos=1)
        print(f"[MQTT] Published → emotion={emotion}, mode={mode}")

    def publish_command(self, command: str):
        """Send raw command to ESP32, e.g. 'BREAK_REMINDER', 'EMERGENCY'."""
        self.client.publish(TOPIC_MODE, command, qos=1)
        print(f"[MQTT] Command sent: {command}")

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            # Subscribe to all ESP32 sensor topics
            for topic in [TOPIC_SENSOR_LDR, TOPIC_SENSOR_PIR, TOPIC_SENSOR_DHT, TOPIC_ENERGY, TOPIC_ALERT]:
                client.subscribe(topic, qos=1)
                print(f"[MQTT] Subscribed to {topic}")
        else:
            print(f"[MQTT] Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"[MQTT] Disconnected (rc={rc}). Will auto-reconnect...")

    def _on_message(self, client, userdata, msg):
        topic   = msg.topic
        payload = msg.payload.decode("utf-8").strip()

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = payload   # plain string value

        # Update internal state
        if topic == TOPIC_SENSOR_LDR:
            self.ldr_value = float(data) if isinstance(data, (str, int, float)) else data.get("value")
        elif topic == TOPIC_SENSOR_PIR:
            self.pir_value = bool(int(data)) if isinstance(data, str) else data
        elif topic == TOPIC_SENSOR_DHT:
            if isinstance(data, dict):
                self.temperature = data.get("temp")
                self.humidity    = data.get("humidity")
        elif topic == TOPIC_ENERGY:
            self.energy_kwh = float(data) if isinstance(data, (str, int, float)) else data.get("kwh")
        elif topic == TOPIC_ALERT:
            print(f"[ALERT] {data}")
            if self.on_alert:
                self.on_alert(str(data))

        # Fire external callback
        if self.on_sensor_update:
            self.on_sensor_update({
                "ldr": self.ldr_value,
                "pir": self.pir_value,
                "temperature": self.temperature,
                "humidity": self.humidity,
                "energy_kwh": self.energy_kwh,
            })

    def get_sensor_snapshot(self) -> dict:
        return {
            "ldr": self.ldr_value,
            "pir": self.pir_value,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "energy_kwh": self.energy_kwh,
            "ts": int(time.time()),
        }


# ─── Entry Point (manual test) ────────────────────────────────────────────────
if __name__ == "__main__":
    client = MQTTClient()
    client.connect()

    print("Sending test emotion: stressed → CALM mode")
    client.publish_emotion("stressed", "CALM")
    time.sleep(2)

    print("Sending test emotion: sleepy → RELAX mode")
    client.publish_emotion("sleepy", "RELAX")
    time.sleep(2)

    print("Listening for sensor data for 10 seconds...")
    time.sleep(10)

    client.disconnect()
