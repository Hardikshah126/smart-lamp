"""
infer.py
Real-time emotion + MQTT + REAL sensor → ThingSpeak
"""

import sys
import os
sys.path.append(os.path.abspath("../cloud"))

import cv2
import numpy as np
import tensorflow as tf
import time
from collections import deque

from preprocess import preprocess_frame
from thingspeak_pusher import ThingSpeakPusher

# ─── CONFIG ─────────────────────────
MODEL_PATH = "model.h5"
LABELS = ["happy", "stressed", "sleepy"]

CONFIDENCE_THRESHOLD = 0.35
SMOOTHING_WINDOW = 10
INFERENCE_INTERVAL = 0.5

EMOTION_TO_MODE = {
    "happy": "FOCUS",
    "stressed": "CALM",
    "sleepy": "RELAX",
}

def load_model(path):
    print(f"[INFO] Loading model from {path}...")
    model = tf.keras.models.load_model(path)
    print("[INFO] Model loaded.")
    return model


def majority_vote(history):
    from collections import Counter
    return Counter(history).most_common(1)[0][0] if history else "unknown"


def run_inference(model, mqtt_client=None, cloud=None):

    cap = cv2.VideoCapture(0)
    history = deque(maxlen=SMOOTHING_WINDOW)

    last_infer_time = 0
    last_cloud_push = 0
    last_sent_emotion = None

    current_emotion = "unknown"
    current_confidence = 0.0

    print("[INFO] Running...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()

        # ─── AI INFERENCE ───
        if now - last_infer_time >= INFERENCE_INTERVAL:

            processed, _ = preprocess_frame(frame)

            if processed is not None:
                inp = np.expand_dims(processed, axis=0)
                preds = model.predict(inp, verbose=0)[0]

                confidence = float(np.max(preds))
                label_idx = int(np.argmax(preds))

                if confidence >= CONFIDENCE_THRESHOLD:
                    history.append(LABELS[label_idx])
                else:
                    history.append("unknown")

                current_emotion = majority_vote(history)
                current_confidence = confidence
                last_infer_time = now

                # MQTT send
                if mqtt_client and current_emotion in EMOTION_TO_MODE:
                    if current_emotion != last_sent_emotion:
                        mode = EMOTION_TO_MODE[current_emotion]
                        mqtt_client.publish_emotion(current_emotion, mode)
                        last_sent_emotion = current_emotion

        # ─── REAL SENSOR → THINGSPEAK ───
        if cloud and mqtt_client and (now - last_cloud_push >= 15):

            ldr = mqtt_client.ldr_value
            temp = mqtt_client.temperature
            humidity = mqtt_client.humidity
            energy = mqtt_client.energy_kwh
            pir = mqtt_client.pir_value

            if None not in (ldr, temp, humidity, energy, pir):

                print("☁️ Sending REAL sensor data...")

                cloud.push(
                    ldr=ldr,
                    temperature=temp,
                    humidity=humidity,
                    energy_kwh=energy,
                    emotion=current_emotion,
                    pir=pir
                )

                last_cloud_push = now
            else:
                print("⚠️ Waiting for sensor data...")

        # ─── UI ───
        cv2.putText(frame, f"{current_emotion} ({current_confidence:.0%})",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

        cv2.imshow("Smart Lamp", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ─── MAIN ─────────────────────────
if __name__ == "__main__":

    # MQTT
    import sys
    sys.path.append("../edge")
    from mqtt_client import MQTTClient

    mqtt = MQTTClient()
    mqtt.connect()

    # Cloud
    cloud = ThingSpeakPusher()

    # Model
    model = load_model(MODEL_PATH)

    # Run
    run_inference(model, mqtt_client=mqtt, cloud=cloud)