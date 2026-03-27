# 💡 Smart Adaptive IoT Lamp — Software

> AI + IoT system for human-aware adaptive lighting.  
> Built at SRM IST, Kattankulathur for students and remote workers.

---

## Project Structure

```
smart-lamp/
├── ml/                    ← Emotion detection CNN
│   ├── preprocess.py      ← Face detection + normalization
│   ├── train.py           ← Model training script
│   ├── infer.py           ← Real-time webcam inference
│   └── requirements.txt
│
├── edge/                  ← Runs on your laptop / Pi
│   ├── emotion_engine.py  ← Main process (camera → MQTT)
│   ├── mqtt_client.py     ← Talks to ESP32 via MQTT
│   └── requirements.txt
│
├── cloud/                 ← Cloud integrations
│   ├── thingspeak_pusher.py  ← Pushes data to ThingSpeak
│   └── blynk_notifier.py    ← Push notifications via Blynk
│
├── backend/               ← FastAPI REST server
│   ├── main.py            ← API endpoints for dashboard
│   └── requirements.txt
│
└── dashboard/             ← React web dashboard
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   └── components/
    │       ├── StatusCards.jsx
    │       ├── EnergyChart.jsx
    │       ├── EmotionChart.jsx
    │       ├── ModeControl.jsx
    │       └── AlertBanner.jsx
    └── package.json
```

---

## ⚡ Quick Setup (Do This Once)

### 1. Clone & open in VS Code
```bash
git clone https://github.com/YOUR_USERNAME/smart-lamp.git
cd smart-lamp
code .
```

### 2. Python virtual environment (do this once, use for all Python folders)
```bash
python -m venv venv

# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. Install all Python packages
```bash
pip install -r ml/requirements.txt
pip install -r edge/requirements.txt
pip install -r backend/requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Open .env and fill in your ThingSpeak + Blynk keys
```

### 5. Install React dashboard
```bash
cd dashboard
npm install
```

---

## 🧠 Step 1 — Train the Emotion Model

### Get a dataset
- Download **FER-2013** from Kaggle: https://www.kaggle.com/datasets/msambare/fer2013
- Or collect your own webcam images (use `preprocess.py` to test face detection)
- Organize it as:
```
ml/data/
  happy/     ← ~500 images
  stressed/  ← ~500 images
  sleepy/    ← ~500 images
```

### Train
```bash
cd ml
python train.py --data ./data --epochs 30
```
- Best model auto-saved to `ml/model.h5`
- TFLite version auto-saved to `ml/model.tflite` (for Raspberry Pi)
- Training curve saved to `training_curves.png`

### Test inference
```bash
python infer.py
# Opens webcam window — shows detected emotion live
```

---

## 📡 Step 2 — Connect to Your Teammate's ESP32

Tell your teammate to use these **exact MQTT topics**:

| Topic | Direction | Payload |
|---|---|---|
| `smartlamp/emotion` | Python → ESP32 | JSON: `{"emotion":"stressed","mode":"CALM"}` |
| `smartlamp/mode` | Python → ESP32 | Plain string: `CALM` / `FOCUS` / `RELAX` |
| `smartlamp/sensor/ldr` | ESP32 → Python | Number: `512` |
| `smartlamp/sensor/pir` | ESP32 → Python | `0` or `1` |
| `smartlamp/sensor/dht` | ESP32 → Python | JSON: `{"temp":28.5,"humidity":60}` |
| `smartlamp/energy` | ESP32 → Python | Number in kWh |
| `smartlamp/alert` | ESP32 → Python | String: `HIGH_TEMP:45.2` |

**Broker:** `broker.hivemq.com` port `1883` (free, no auth needed for testing)

### Run the main edge engine
```bash
cd edge
python emotion_engine.py
```
This starts the webcam, runs emotion detection, and sends commands to the ESP32 automatically.

---

## ☁️ Step 3 — Cloud Setup

### ThingSpeak
1. Go to https://thingspeak.com → Sign up free
2. Create a new Channel → add 6 fields (LDR, Temp, Humidity, Energy, Emotion, PIR)
3. Copy your **Write API Key** and **Channel ID** into `.env`

### Blynk
1. Go to https://blynk.cloud → Sign up free
2. Create a Template → Device → copy your **Auth Token** into `.env`
3. In the Blynk mobile app: add widgets on pins V0–V5 (see `blynk_notifier.py` for mapping)

---

## 🖥️ Step 4 — Run the Dashboard

### Start the backend
```bash
cd backend
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### Start the React dashboard
```bash
cd dashboard
npm start
# Opens: http://localhost:3000
```

> **Note:** Dashboard works with mock data even without ThingSpeak configured.  
> Just run the backend and it auto-generates sample data for testing.

---

## 🔁 Daily Dev Workflow

Open 3 VS Code terminals:

```
Terminal 1 → cd edge   → python emotion_engine.py
Terminal 2 → cd backend → uvicorn main:app --reload
Terminal 3 → cd dashboard → npm start
```

---

## 🎯 Emotion → Lighting Mode Map

| Detected Emotion | Lighting Mode | LED Color | Why |
|---|---|---|---|
| Happy | FOCUS | Bright White | Maintain concentration |
| Stressed | CALM | Cool Blue | Reduce mental stimulation |
| Sleepy | RELAX | Warm Yellow | Ease into rest |
| Unknown / No face | (no change) | — | Confidence too low |

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/summary` | Latest snapshot — emotion, temp, energy |
| GET | `/api/energy?limit=48` | Energy + sensor history |
| GET | `/api/emotion/history?limit=50` | Emotion timeline |
| GET | `/api/energy/weekly` | Total kWh last 7 days |
| GET | `/api/health` | Health check |

---

## 🛠️ VS Code Extensions to Install

- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Jupyter** (ms-toolsai.jupyter)
- **ES7+ React/Redux Snippets** (dsznajder.es7-react-js-snippets)
- **Prettier** (esbenp.prettier-vscode)
- **Thunder Client** (rangav.vscode-thunder-client) — test your API endpoints

---

## 🔥 Build Order (Fastest Path to Demo)

| Day | Task |
|---|---|
| Day 1 | Set up venv, get FER-2013 dataset, run `train.py` |
| Day 2 | Test `infer.py` with webcam, tune confidence threshold |
| Day 3 | Connect MQTT with teammate's ESP32, test live mode switching |
| Day 4 | Configure ThingSpeak, run `thingspeak_pusher.py` |
| Day 5 | Start backend + dashboard, verify charts show real data |
| Day 6 | Configure Blynk push notifications, test emergency alerts |
| Day 7 | End-to-end demo + polish |
