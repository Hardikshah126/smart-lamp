"""
thingspeak_pusher.py
Pushes sensor data to ThingSpeak cloud for the dashboard.

ThingSpeak Field Mapping:
  Field 1 → LDR (ambient light, 0–1023)
  Field 2 → Temperature (°C)
  Field 3 → Humidity (%)
  Field 4 → Energy (kWh)
  Field 5 → Emotion index (0=happy, 1=stressed, 2=sleepy, -1=unknown)
  Field 6 → PIR presence (0 or 1)

Setup:
  1. Create account at https://thingspeak.com
  2. Create a Channel with 6 fields
  3. Copy your Write API Key below
"""

import requests
import time
from datetime import datetime

# ─── Config ─────────────────────────────────────────────────────────────
THINGSPEAK_WRITE_API_KEY = "0C2VPYX5MFWP7FYE"   # ← paste your key
THINGSPEAK_CHANNEL_ID    = "3311540"           # ← paste your channel ID
THINGSPEAK_READ_API_KEY  = "OLKWG52C5YOSUAV7"    # ← for dashboard reads

BASE_URL  = "https://api.thingspeak.com"
UPDATE_URL = f"{BASE_URL}/update"
READ_URL   = f"{BASE_URL}/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"

EMOTION_INDEX = {"happy": 0, "stressed": 1, "sleepy": 2, "unknown": -1}
RATE_LIMIT_SECONDS = 15   # ThingSpeak free tier allows 1 update per 15 seconds


class ThingSpeakPusher:
    def __init__(self):
        self.last_push = 0
        self.api_key = THINGSPEAK_WRITE_API_KEY
        print(f"[CLOUD] ThingSpeak pusher initialized. Channel: {THINGSPEAK_CHANNEL_ID}")

    def push(self, ldr=None, temperature=None, humidity=None,
             energy_kwh=None, emotion="unknown", pir=None):
        """
        Push sensor values to ThingSpeak.
        Respects the 15-second rate limit.
        """
        now = time.time()
        if now - self.last_push < RATE_LIMIT_SECONDS:
            wait = RATE_LIMIT_SECONDS - (now - self.last_push)
            print(f"[CLOUD] Rate limit: waiting {wait:.1f}s before push.")
            time.sleep(wait)

        params = {"api_key": self.api_key}
        if ldr         is not None: params["field1"] = round(ldr, 2)
        if temperature is not None: params["field2"] = round(temperature, 2)
        if humidity    is not None: params["field3"] = round(humidity, 2)
        if energy_kwh  is not None: params["field4"] = round(energy_kwh, 4)
        if emotion:                  params["field5"] = EMOTION_INDEX.get(emotion, -1)
        if pir         is not None: params["field6"] = int(bool(pir))

        try:
            resp = requests.get(UPDATE_URL, params=params, timeout=10)
            if resp.status_code == 200 and resp.text != "0":
                self.last_push = time.time()
                print(f"[CLOUD] Pushed → Entry #{resp.text} | {datetime.now().strftime('%H:%M:%S')}")
                return True
            else:
                print(f"[CLOUD] Push failed: status={resp.status_code}, body={resp.text}")
                return False
        except requests.RequestException as e:
            print(f"[CLOUD] Network error: {e}")
            return False

    def fetch_recent(self, results: int = 100) -> list:
        """
        Fetch the last N entries from ThingSpeak.
        Returns a list of dicts with parsed sensor values.
        """
        params = {"api_key": THINGSPEAK_READ_API_KEY, "results": results}
        try:
            resp = requests.get(READ_URL, params=params, timeout=10)
            resp.raise_for_status()
            feeds = resp.json().get("feeds", [])

            parsed = []
            for entry in feeds:
                parsed.append({
                    "created_at":  entry.get("created_at"),
                    "ldr":         _safe_float(entry.get("field1")),
                    "temperature": _safe_float(entry.get("field2")),
                    "humidity":    _safe_float(entry.get("field3")),
                    "energy_kwh":  _safe_float(entry.get("field4")),
                    "emotion_idx": _safe_int(entry.get("field5")),
                    "pir":         bool(_safe_int(entry.get("field6"))),
                })
            return parsed
        except Exception as e:
            print(f"[CLOUD] Fetch failed: {e}")
            return []

    def fetch_weekly_energy(self) -> float:
        """Returns total energy consumed in the last 7 days (kWh)."""
        entries = self.fetch_recent(results=10000)
        total = sum(e["energy_kwh"] for e in entries if e["energy_kwh"] is not None)
        return round(total, 3)


def _safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


# ─── Entry Point (test) ───────────────────────────────────────────────────────
if __name__ == "__main__":
    pusher = ThingSpeakPusher()

    print("Pushing test data...")
    pusher.push(
        ldr=512,
        temperature=28.5,
        humidity=60.0,
        energy_kwh=0.0023,
        emotion="stressed",
        pir=True,
    )

    print("\nFetching recent data...")
    data = pusher.fetch_recent(results=5)
    for entry in data:
        print(entry)
