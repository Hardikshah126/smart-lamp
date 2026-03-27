"""
infer_espcam.py
Reads video stream from ESP32-CAM instead of laptop webcam.
The ESP32-CAM publishes its IP via MQTT automatically.
Run: python infer_espcam.py
"""

import cv2
import numpy as np
import tensorflow as tf
import time
import sys
import threading
from pathlib import Path
from collections import deque, Counter

sys.path.append(str(Path(__file__).parent.parent / "edge"))
from mqtt_client import MQTTClient

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_PATH           = "model.h5"
LABELS               = ["happy", "stressed", "sleepy"]
CONFIDENCE_THRESHOLD = 0.40
SMOOTHING_WINDOW     = 8
INFERENCE_INTERVAL   = 0.5

EMOTION_TO_MODE = {
    "happy":    "FOCUS",
    "stressed": "CALM",
    "sleepy":   "RELAX",
}

# MQTT topic where ESP32-CAM publishes its stream URL
TOPIC_CAM_IP = "smartlamp/camera/ip"

# Fallback — paste your ESP32-CAM IP here if MQTT auto-detect fails
ESP32_CAM_FALLBACK_IP = "192.168.x.x"   # ← change if needed


# ── Face detector ─────────────────────────────────────────────────────────────
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# ── Get stream URL from MQTT ──────────────────────────────────────────────────
def get_stream_url_from_mqtt(timeout=10) -> str:
    """Subscribe to MQTT and wait for ESP32-CAM to publish its stream URL."""
    stream_url = [None]

    import paho.mqtt.client as mqtt_lib

    def on_message(client, userdata, msg):
        url = msg.payload.decode("utf-8").strip()
        if url.startswith("http://"):
            stream_url[0] = url
            print(f"[INFO] Got stream URL from MQTT: {url}")

    client = mqtt_lib.Client(client_id="stream-url-fetcher")
    client.on_message = on_message
    client.connect("broker.hivemq.com", 1883, 60)
    client.subscribe(TOPIC_CAM_IP, qos=1)
    client.loop_start()

    deadline = time.time() + timeout
    while stream_url[0] is None and time.time() < deadline:
        time.sleep(0.2)

    client.loop_stop()
    client.disconnect()

    if stream_url[0]:
        return stream_url[0]
    else:
        fallback = f"http://{ESP32_CAM_FALLBACK_IP}:81/stream"
        print(f"[WARNING] MQTT timeout. Using fallback: {fallback}")
        print(f"[TIP] Check Serial Monitor for the correct IP and update ESP32_CAM_FALLBACK_IP")
        return fallback


# ── Main inference loop ───────────────────────────────────────────────────────
def run(stream_url: str, mqtt_client=None):
    print(f"[INFO] Connecting to stream: {stream_url}")
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print(f"[ERROR] Cannot open stream at {stream_url}")
        print("[TIP] Make sure ESP32-CAM is powered and on the same WiFi network.")
        print("[TIP] Try opening the URL in your browser first to verify it works.")
        return

    print("[INFO] Stream connected! Press Q to quit.")

    model    = tf.keras.models.load_model(MODEL_PATH)
    history  = deque(maxlen=SMOOTHING_WINDOW)
    last_infer   = 0
    current_emotion    = "unknown"
    current_confidence = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Frame read failed — reconnecting...")
            time.sleep(1)
            cap = cv2.VideoCapture(stream_url)
            continue

        now = time.time()

        if now - last_infer >= INFERENCE_INTERVAL:
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60,60))

            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

                face_crop  = gray[y:y+h, x:x+w]
                face_small = cv2.resize(face_crop, (48,48)).astype("float32") / 255.0
                inp = np.expand_dims(np.expand_dims(face_small, -1), 0)

                preds      = model.predict(inp, verbose=0)[0]
                confidence = float(np.max(preds))
                label_idx  = int(np.argmax(preds))

                if confidence >= CONFIDENCE_THRESHOLD:
                    history.append(LABELS[label_idx])
                else:
                    history.append("unknown")

                current_emotion    = Counter(history).most_common(1)[0][0]
                current_confidence = confidence

                if mqtt_client and current_emotion in EMOTION_TO_MODE:
                    mqtt_client.publish_emotion(
                        current_emotion, EMOTION_TO_MODE[current_emotion])
            else:
                history.append("unknown")

            last_infer = now

        # Overlay
        color_map = {
            "happy":    (0, 255, 100),
            "stressed": (0, 100, 255),
            "sleepy":   (0, 200, 255),
            "unknown":  (150, 150, 150),
        }
        color = color_map.get(current_emotion, (255,255,255))
        cv2.rectangle(frame, (0,0), (400, 85), (0,0,0), -1)
        cv2.putText(frame, f"Emotion: {current_emotion.upper()}",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        cv2.putText(frame, f"Confidence: {current_confidence:.0%}  |  Mode: {EMOTION_TO_MODE.get(current_emotion,'-')}",
                    (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)

        cv2.imshow("Smart Lamp — ESP32-CAM Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔆 Smart Lamp — ESP32-CAM Inference")
    print("Looking for ESP32-CAM stream URL via MQTT...")

    stream_url = get_stream_url_from_mqtt(timeout=8)

    # Connect MQTT for publishing emotions back
    try:
        mqtt = MQTTClient()
        mqtt.connect()
        print("[MQTT] Connected for emotion publishing.")
    except Exception as e:
        print(f"[WARNING] MQTT publish unavailable: {e}")
        mqtt = None

    run(stream_url, mqtt_client=mqtt)