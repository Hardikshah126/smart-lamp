"""
emotion_engine.py
Main edge process: webcam → emotion detection → MQTT → ESP32 → LED.
Also runs the Pomodoro study timer and pushes data to ThingSpeak.
Run: python emotion_engine.py
"""

import sys
import time
import threading
import cv2
import numpy as np
import tensorflow as tf
from collections import deque
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "ml"))
sys.path.append(str(Path(__file__).parent.parent / "cloud"))

from preprocess import preprocess_frame
from mqtt_client import MQTTClient

# ─── Config ───────────────────────────────────────────────────────────────────
MODEL_PATH          = "../ml/model.h5"
LABELS              = ["happy", "stressed", "sleepy"]
CONFIDENCE_THRESHOLD = 0.65
SMOOTHING_WINDOW    = 10
INFERENCE_INTERVAL  = 0.5    # seconds between inferences
POMODORO_MINUTES    = 45     # study session length before break reminder
ENERGY_PUSH_INTERVAL = 30   # seconds between energy pushes to cloud

EMOTION_TO_MODE = {
    "happy":    "FOCUS",
    "stressed": "CALM",
    "sleepy":   "RELAX",
}


class EmotionEngine:
    def __init__(self):
        print("[ENGINE] Initializing Smart Lamp Emotion Engine...")

        # Load model
        self.model = tf.keras.models.load_model(MODEL_PATH)
        print("[ENGINE] Model loaded.")

        # MQTT
        self.mqtt = MQTTClient()
        self.mqtt.on_sensor_update = self._on_sensor_update
        self.mqtt.on_alert = self._on_alert

        # State
        self.history = deque(maxlen=SMOOTHING_WINDOW)
        self.current_emotion = "unknown"
        self.sensor_data = {}
        self.running = False

        # Pomodoro timer
        self.session_start = time.time()
        self.pomodoro_triggered = False

        # Cloud pusher (optional)
        try:
            from thingspeak_pusher import ThingSpeakPusher
            self.cloud = ThingSpeakPusher()
            print("[ENGINE] ThingSpeak cloud pusher connected.")
        except Exception as e:
            self.cloud = None
            print(f"[ENGINE] Cloud pusher not available: {e}")

    def start(self):
        self.mqtt.connect()
        self.running = True

        # Start background threads
        threading.Thread(target=self._pomodoro_loop, daemon=True).start()
        threading.Thread(target=self._cloud_push_loop, daemon=True).start()

        self._camera_loop()

    def _camera_loop(self):
        cap = cv2.VideoCapture(0)
        last_infer = 0

        print("[ENGINE] Camera started. Press Q to quit.")
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            now = time.time()
            if now - last_infer >= INFERENCE_INTERVAL:
                self._run_inference(frame)
                last_infer = now

            self._draw_overlay(frame)
            cv2.imshow("Smart Lamp - Edge Engine", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.running = False
                break

        cap.release()
        cv2.destroyAllWindows()
        self.mqtt.disconnect()

    def _run_inference(self, frame):
        processed, _ = preprocess_frame(frame)
        if processed is None:
            self.history.append("unknown")
            return

        inp = np.expand_dims(processed, 0)
        preds = self.model.predict(inp, verbose=0)[0]
        confidence = float(np.max(preds))
        label_idx  = int(np.argmax(preds))

        if confidence >= CONFIDENCE_THRESHOLD:
            emotion = LABELS[label_idx]
        else:
            emotion = "unknown"

        self.history.append(emotion)

        from collections import Counter
        smoothed = Counter(self.history).most_common(1)[0][0]

        if smoothed != self.current_emotion and smoothed != "unknown":
            self.current_emotion = smoothed
            mode = EMOTION_TO_MODE.get(smoothed, "FOCUS")
            self.mqtt.publish_emotion(smoothed, mode)
            print(f"[ENGINE] Emotion changed → {smoothed} ({mode})")

    def _pomodoro_loop(self):
        """Fires a break reminder after POMODORO_MINUTES of study."""
        while self.running:
            elapsed = (time.time() - self.session_start) / 60
            if elapsed >= POMODORO_MINUTES and not self.pomodoro_triggered:
                print("[POMODORO] Break time! Sending reminder...")
                self.mqtt.publish_command("BREAK_REMINDER")
                self.pomodoro_triggered = True
            elif elapsed >= POMODORO_MINUTES + 5:
                # Reset for next session
                self.session_start = time.time()
                self.pomodoro_triggered = False
            time.sleep(10)

    def _cloud_push_loop(self):
        """Pushes sensor data to ThingSpeak every ENERGY_PUSH_INTERVAL seconds."""
        while self.running:
            time.sleep(ENERGY_PUSH_INTERVAL)
            if self.cloud and self.sensor_data:
                try:
                    self.cloud.push(
                        ldr=self.sensor_data.get("ldr"),
                        temperature=self.sensor_data.get("temperature"),
                        humidity=self.sensor_data.get("humidity"),
                        energy_kwh=self.sensor_data.get("energy_kwh"),
                        emotion=self.current_emotion,
                    )
                except Exception as e:
                    print(f"[ENGINE] Cloud push failed: {e}")

    def _on_sensor_update(self, data: dict):
        self.sensor_data = data

    def _on_alert(self, message: str):
        print(f"[ALERT] Emergency received: {message}")
        # Blynk notification can be triggered here

    def _draw_overlay(self, frame):
        emotion_colors = {
            "happy":    (0, 255, 100),
            "stressed": (0, 100, 255),
            "sleepy":   (0, 200, 255),
            "unknown":  (150, 150, 150),
        }
        color = emotion_colors.get(self.current_emotion, (255, 255, 255))
        mode  = EMOTION_TO_MODE.get(self.current_emotion, "-")

        cv2.rectangle(frame, (10, 10), (400, 100), (0, 0, 0), -1)
        cv2.putText(frame, f"Emotion: {self.current_emotion.upper()}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv2.putText(frame, f"Mode: {mode}  |  Sensor Temp: {self.sensor_data.get('temperature', '--')}°C",
                    (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        elapsed_min = int((time.time() - self.session_start) / 60)
        cv2.putText(frame, f"Session: {elapsed_min}/{POMODORO_MINUTES} min",
                    (20, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 100), 1)


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = EmotionEngine()
    engine.start()
