import requests
import time
from datetime import datetime

# ─── CONFIG ─────────────────────────────────────────
THINGSPEAK_WRITE_API_KEY = "0C2VPYX5MFWP7FYE"
THINGSPEAK_CHANNEL_ID = "3311540"
THINGSPEAK_READ_API_KEY = "OLKWG52C5YOSUAV7"

UPDATE_URL = "https://api.thingspeak.com/update"
READ_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"

EMOTION_INDEX = {"happy": 0, "stressed": 1, "sleepy": 2, "unknown": -1}
RATE_LIMIT_SECONDS = 15


class ThingSpeakPusher:
    def __init__(self):
        self.last_push = 0
        print(f"[CLOUD] Connected to ThingSpeak Channel {THINGSPEAK_CHANNEL_ID}")

    def push(self, ldr=None, temperature=None, humidity=None,
             energy_kwh=None, emotion="unknown", pir=None):

        now = time.time()
        if now - self.last_push < RATE_LIMIT_SECONDS:
            wait = RATE_LIMIT_SECONDS - (now - self.last_push)
            print(f"[CLOUD] Waiting {wait:.1f}s (rate limit)")
            time.sleep(wait)

        params = {
            "api_key": THINGSPEAK_WRITE_API_KEY
        }

        if ldr is not None:
            params["field1"] = ldr
        if temperature is not None:
            params["field2"] = temperature
        if humidity is not None:
            params["field3"] = humidity
        if energy_kwh is not None:
            params["field4"] = energy_kwh
        if emotion:
            params["field5"] = EMOTION_INDEX.get(emotion, -1)
        if pir is not None:
            params["field6"] = int(pir)

        print("📤 Sending:", params)

        try:
            # ✅ FIXED: use POST
            resp = requests.post(UPDATE_URL, data=params, timeout=10)

            print("Response:", resp.status_code, resp.text)

            if resp.status_code == 200 and resp.text != "0":
                self.last_push = time.time()
                print(f"✅ Uploaded Entry #{resp.text}")
                return True
            else:
                print("❌ Upload failed")
                return False

        except Exception as e:
            print("❌ Error:", e)
            return False

    def fetch_recent(self, results=5):

        params = {
            "api_key": THINGSPEAK_READ_API_KEY,
            "results": results
        }

        try:
            # ✅ FIXED: use READ_URL + GET
            resp = requests.get(READ_URL, params=params, timeout=10)

            print("📡 Fetch URL:", resp.url)

            resp.raise_for_status()
            data = resp.json()

            feeds = data.get("feeds", [])

            print("✅ Data fetched")

            return feeds

        except Exception as e:
            print("❌ Fetch failed:", e)
            return []


# ─── TEST ─────────────────────────────────────────
if __name__ == "__main__":
    pusher = ThingSpeakPusher()

    print("\n--- PUSH TEST ---")
    pusher.push(
        ldr=500,
        temperature=27.5,
        humidity=55,
        energy_kwh=0.002,
        emotion="happy",
        pir=1
    )

    print("\n--- FETCH TEST ---")
    data = pusher.fetch_recent()

    for entry in data:
        print(entry)