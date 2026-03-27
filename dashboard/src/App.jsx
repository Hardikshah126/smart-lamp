// App.jsx
// Main dashboard for Smart Adaptive IoT Lamp
// Run: npm install && npm start

import { useState, useEffect, useCallback } from "react";
import StatusCards from "./components/StatusCards";
import EnergyChart from "./components/EnergyChart";
import EmotionChart from "./components/EmotionChart";
import ModeControl from "./components/ModeControl";
import AlertBanner from "./components/AlertBanner";
import "./App.css";

const API_BASE = "http://localhost:8000/api";
const REFRESH_INTERVAL = 10000; // 10 seconds

export default function App() {
  const [summary, setSummary]         = useState(null);
  const [energyData, setEnergyData]   = useState([]);
  const [emotionData, setEmotionData] = useState([]);
  const [alert, setAlert]             = useState(null);
  const [loading, setLoading]         = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [sumRes, energyRes, emotionRes] = await Promise.all([
        fetch(`${API_BASE}/summary`),
        fetch(`${API_BASE}/energy?limit=48`),
        fetch(`${API_BASE}/emotion/history?limit=50`),
      ]);

      if (sumRes.ok)    setSummary(await sumRes.json());
      if (energyRes.ok) setEnergyData(await energyRes.json());
      if (emotionRes.ok) setEmotionData(await emotionRes.json());

      // Check temperature alert
      const s = await sumRes.clone().json().catch(() => null);
      if (s?.temperature && s.temperature > 45) {
        setAlert(`⚠️ High Temperature Alert: ${s.temperature}°C detected!`);
      } else {
        setAlert(null);
      }
    } catch (err) {
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchAll]);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>Connecting to Smart Lamp...</p>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <span className="lamp-icon">💡</span>
          <div>
            <h1>Smart Adaptive Lamp</h1>
            <p className="subtitle">AI-Powered Lighting Dashboard</p>
          </div>
        </div>
        <div className="header-right">
          <div className={`status-dot ${summary?.pir_active ? "active" : "idle"}`} />
          <span>{summary?.pir_active ? "User Present" : "Room Empty"}</span>
          <span className="last-update">
            Updated: {summary?.last_updated ? new Date(summary.last_updated).toLocaleTimeString() : "--"}
          </span>
        </div>
      </header>

      {/* Alert Banner */}
      {alert && <AlertBanner message={alert} onClose={() => setAlert(null)} />}

      <main className="main">
        {/* Status Cards Row */}
        <StatusCards summary={summary} />

        {/* Charts Row */}
        <div className="charts-row">
          <div className="chart-card wide">
            <h2>Energy Consumption</h2>
            <EnergyChart data={energyData} />
          </div>
          <div className="chart-card">
            <h2>Mood History</h2>
            <EmotionChart data={emotionData} />
          </div>
        </div>

        {/* Manual Mode Control */}
        <ModeControl />
      </main>
    </div>
  );
}
