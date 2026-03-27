"""
blynk_notifier.py
Sends push notifications via Blynk Cloud (temperature alerts, break reminders).

Setup:
  1. Create account at https://blynk.cloud
  2. Create a new Template → Device → get BLYNK_AUTH_TOKEN
  3. Add a Notification widget in your Blynk app
  4. Paste your token below
"""

import requests
import time

# ─── Config ───────────────────────────────────────────────────────────────────
BLYNK_AUTH_TOKEN = "YOUR_BLYNK_AUTH_TOKEN_HERE"   # ← paste your token
BLYNK_API_BASE   = "https://blynk.cloud/external/api"

# Virtual pins (configure matching widgets in Blynk app)
PIN_EMOTION    = "V0"    # String — current emotion
PIN_MODE       = "V1"    # String — lighting mode
PIN_TEMP       = "V2"    # Number — temperature °C
PIN_ENERGY     = "V3"    # Number — energy kWh
PIN_PIR        = "V4"    # 0 or 1 — presence
PIN_LDR        = "V5"    # 0–1023 — ambient light


class BlynkNotifier:
    def __init__(self, token: str = BLYNK_AUTH_TOKEN):
        self.token = token
        self.last_notify = 0
        self.notify_cooldown = 60   # seconds between repeated alerts

    # ── Notify ────────────────────────────────────────────────────────────────
    def notify(self, message: str) -> bool:
        """Send a push notification to the Blynk mobile app."""
        now = time.time()
        if now - self.last_notify < self.notify_cooldown:
            print(f"[BLYNK] Notify throttled. {int(self.notify_cooldown - (now - self.last_notify))}s remaining.")
            return False

        url = f"{BLYNK_API_BASE}/notify?token={self.token}&body={requests.utils.quote(message)}"
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                self.last_notify = time.time()
                print(f"[BLYNK] Notification sent: {message}")
                return True
            else:
                print(f"[BLYNK] Notify failed: {resp.status_code} {resp.text}")
                return False
        except requests.RequestException as e:
            print(f"[BLYNK] Network error: {e}")
            return False

    def temperature_alert(self, temp: float):
        self.notify(f"🚨 Smart Lamp Alert: Temperature is {temp:.1f}°C — check the device!")

    def break_reminder(self):
        self.notify("⏱️ Smart Lamp: Time for a break! You've been studying for 45 minutes.")

    # ── Update Virtual Pins ───────────────────────────────────────────────────
    def update_pin(self, pin: str, value) -> bool:
        """Write a value to a Blynk virtual pin (updates app widgets)."""
        url = f"{BLYNK_API_BASE}/update?token={self.token}&{pin}={value}"
        try:
            resp = requests.get(url, timeout=8)
            success = resp.status_code == 200
            if not success:
                print(f"[BLYNK] Pin update failed: {pin}={value} → {resp.status_code}")
            return success
        except requests.RequestException as e:
            print(f"[BLYNK] Pin update error: {e}")
            return False

    def push_sensor_data(self, emotion=None, mode=None, temperature=None,
                         energy_kwh=None, pir=None, ldr=None):
        """Push all sensor values to Blynk virtual pins in one batch."""
        updates = []
        if emotion     is not None: updates.append((PIN_EMOTION, emotion))
        if mode        is not None: updates.append((PIN_MODE, mode))
        if temperature is not None: updates.append((PIN_TEMP, round(temperature, 1)))
        if energy_kwh  is not None: updates.append((PIN_ENERGY, round(energy_kwh, 4)))
        if pir         is not None: updates.append((PIN_PIR, int(bool(pir))))
        if ldr         is not None: updates.append((PIN_LDR, round(ldr, 0)))

        results = [self.update_pin(pin, val) for pin, val in updates]
        print(f"[BLYNK] Pushed {sum(results)}/{len(results)} pin updates.")
        return all(results)


# ─── Entry Point (test) ───────────────────────────────────────────────────────
if __name__ == "__main__":
    notifier = BlynkNotifier()

    print("Sending test notification...")
    notifier.notify("✅ Smart Lamp connected and running!")

    print("Pushing test sensor data to pins...")
    notifier.push_sensor_data(
        emotion="stressed",
        mode="CALM",
        temperature=29.5,
        energy_kwh=0.003,
        pir=True,
        ldr=400,
    )
