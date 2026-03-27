"""
infer.py
Real-time emotion detection from webcam using the trained model.
Publishes emotion labels via MQTT to the ESP32.
Run: python infer.py
"""

import cv2
import numpy as np
import tensorflow as tf
import time
from collections import deque

from preprocess import preprocess_frame

# ─── Config ───────────────────────────────────────────────────────────────────
MODEL_PATH = "model.h5"
LABELS = ["happy", "stressed", "sleepy"]
CONFIDENCE_THRESHOLD = 0.35 # below this → default "neutral" / no change
SMOOTHING_WINDOW = 10          # rolling majority vote over last N frames
INFERENCE_INTERVAL = 0.5       # run inference every 0.5s to save CPU

# Lighting color map sent to ESP32 (matches your product doc)
EMOTION_TO_MODE = {
    "happy":    "FOCUS",    # Bright white
    "stressed": "CALM",     # Blue
    "sleepy":   "RELAX",    # Warm yellow
}


# ─── Load Model ───────────────────────────────────────────────────────────────
def load_model(path: str):
    print(f"[INFO] Loading model from {path}...")
    model = tf.keras.models.load_model(path)
    print("[INFO] Model loaded.")
    return model


# ─── Smoothing ────────────────────────────────────────────────────────────────
def majority_vote(history: deque) -> str:
    if not history:
        return "unknown"
    from collections import Counter
    return Counter(history).most_common(1)[0][0]


# ─── Inference Loop ───────────────────────────────────────────────────────────
def run_inference(model, mqtt_client=None):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam.")

    history = deque(maxlen=SMOOTHING_WINDOW)
    last_infer_time = 0
    current_emotion = "unknown"
    current_confidence = 0.0

    print("[INFO] Starting real-time inference. Press Q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()

        # Run inference at limited rate
        if now - last_infer_time >= INFERENCE_INTERVAL:
            processed, face_crop = preprocess_frame(frame)

            if processed is not None:
                inp = np.expand_dims(processed, axis=0)   # (1, 48, 48, 1)
                preds = model.predict(inp, verbose=0)[0]   # (3,)
                confidence = float(np.max(preds))
                label_idx = int(np.argmax(preds))

                if confidence >= CONFIDENCE_THRESHOLD:
                    detected = LABELS[label_idx]
                    history.append(detected)
                else:
                    history.append("unknown")

                current_emotion = majority_vote(history)
                current_confidence = confidence
                last_infer_time = now

                # Publish to MQTT if client is connected
                if mqtt_client and current_emotion in EMOTION_TO_MODE:
                    mode = EMOTION_TO_MODE[current_emotion]
                    mqtt_client.publish_emotion(current_emotion, mode)

        # ── Overlay on frame ──────────────────────────────────────────────
        color_map = {"happy": (0, 255, 100), "stressed": (0, 100, 255), "sleepy": (0, 200, 255), "unknown": (150, 150, 150)}
        color = color_map.get(current_emotion, (255, 255, 255))

        cv2.rectangle(frame, (10, 10), (380, 80), (0, 0, 0), -1)
        cv2.putText(frame, f"Emotion: {current_emotion.upper()}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv2.putText(frame, f"Confidence: {current_confidence:.0%}", (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Smart Lamp - Emotion Engine", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Inference stopped.")


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Optional: import MQTT client for live hardware control
    try:
        import sys
        sys.path.append("../edge")
        from mqtt_client import MQTTClient
        mqtt = MQTTClient()
        mqtt.connect()
    except Exception as e:
        print(f"[WARNING] MQTT not connected: {e}. Running in display-only mode.")
        mqtt = None

    model = load_model(MODEL_PATH)
    run_inference(model, mqtt_client=mqtt)
