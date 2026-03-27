"""
main.py
FastAPI backend — bridges ThingSpeak data to the React dashboard.
Run: uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

import sys
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from thingspeak_pusher import ThingSpeakPusher, EMOTION_INDEX
import time

sys.path.append(str(Path(__file__).parent.parent / "cloud"))

try:
    from thingspeak_pusher import ThingSpeakPusher, EMOTION_INDEX
    cloud = ThingSpeakPusher()
except Exception:
    cloud = None
    print("[BACKEND] ThingSpeak not configured — returning mock data.")

app = FastAPI(
    title="Smart Lamp API",
    description="Backend for Smart Adaptive IoT Lamp dashboard",
    version="1.0.0",
)

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reverse emotion index
IDX_TO_EMOTION = {v: k for k, v in EMOTION_INDEX.items()} if cloud else {
    0: "happy", 1: "stressed", 2: "sleepy", -1: "unknown"
}


# ─── Schemas ──────────────────────────────────────────────────────────────────
class SensorEntry(BaseModel):
    created_at: Optional[str]
    ldr: Optional[float]
    temperature: Optional[float]
    humidity: Optional[float]
    energy_kwh: Optional[float]
    emotion: Optional[str]
    pir: Optional[bool]


class DashboardSummary(BaseModel):
    current_emotion: str
    current_mode: str
    temperature: Optional[float]
    humidity: Optional[float]
    ldr: Optional[float]
    total_energy_kwh: float
    pir_active: bool
    last_updated: str


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Smart Lamp API is running", "docs": "/docs"}


@app.get("/api/summary", response_model=DashboardSummary)
def get_summary():
    """Latest snapshot for the top-of-dashboard status cards."""
    if cloud:
        entries = cloud.fetch_recent(results=5)
        latest = entries[-1] if entries else {}
        emotion_idx = latest.get("emotion_idx", -1)
        emotion = IDX_TO_EMOTION.get(emotion_idx, "unknown")
    else:
        # Mock data for development
        latest = {"ldr": 512.0, "temperature": 28.5, "humidity": 60.0,
                  "energy_kwh": 0.005, "pir": True}
        emotion = "stressed"

    EMOTION_TO_MODE = {"happy": "FOCUS", "stressed": "CALM", "sleepy": "RELAX", "unknown": "AUTO"}

    return DashboardSummary(
        current_emotion=emotion,
        current_mode=EMOTION_TO_MODE.get(emotion, "AUTO"),
        temperature=latest.get("temperature"),
        humidity=latest.get("humidity"),
        ldr=latest.get("ldr"),
        total_energy_kwh=latest.get("energy_kwh") or 0.0,
        pir_active=bool(latest.get("pir")),
        last_updated=datetime.utcnow().isoformat(),
    )


@app.get("/api/energy", response_model=List[SensorEntry])
def get_energy_history(limit: int = 100):
    """Returns energy + sensor history for charts."""
    if cloud:
        raw = cloud.fetch_recent(results=limit)
        entries = []
        for r in raw:
            entries.append(SensorEntry(
                created_at=r["created_at"],
                ldr=r["ldr"],
                temperature=r["temperature"],
                humidity=r["humidity"],
                energy_kwh=r["energy_kwh"],
                emotion=IDX_TO_EMOTION.get(r["emotion_idx"], "unknown"),
                pir=r["pir"],
            ))
        return entries
    else:
        # Mock 24 data points
        import random
        now = time.time()
        return [
            SensorEntry(
                created_at=datetime.fromtimestamp(now - i * 3600).isoformat(),
                ldr=random.uniform(200, 900),
                temperature=random.uniform(24, 32),
                humidity=random.uniform(50, 75),
                energy_kwh=random.uniform(0.001, 0.008),
                emotion=random.choice(["happy", "stressed", "sleepy"]),
                pir=random.choice([True, False]),
            )
            for i in range(24)
        ]


@app.get("/api/energy/weekly")
def get_weekly_energy():
    """Total kWh consumed in the past week."""
    if cloud:
        total = cloud.fetch_weekly_energy()
    else:
        total = 0.342   # mock
    return {"total_kwh": total, "period": "7 days"}


@app.get("/api/emotion/history")
def get_emotion_history(limit: int = 50):
    """Emotion timeline for mood chart."""
    if cloud:
        raw = cloud.fetch_recent(results=limit)
        return [
            {
                "time": r["created_at"],
                "emotion": IDX_TO_EMOTION.get(r["emotion_idx"], "unknown"),
                "emotion_idx": r["emotion_idx"],
            }
            for r in raw
        ]
    else:
        import random
        now = time.time()
        return [
            {
                "time": datetime.fromtimestamp(now - i * 300).isoformat(),
                "emotion": random.choice(["happy", "stressed", "sleepy"]),
                "emotion_idx": random.randint(0, 2),
            }
            for i in range(50)
        ]


@app.get("/api/health")
def health_check():
    return {"status": "ok", "cloud_connected": cloud is not None}
