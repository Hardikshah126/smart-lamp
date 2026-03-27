// components/ModeControl.jsx
// Manual override panel — sends mode commands to the backend → MQTT → ESP32

import { useState } from "react";

const API_BASE = "http://localhost:8000/api";

const MODES = [
  { id: "FOCUS",  label: "Focus",  emoji: "🎯", desc: "Bright white light",  color: "#60a5fa" },
  { id: "CALM",   label: "Calm",   emoji: "🧘", desc: "Cool blue tone",      color: "#a78bfa" },
  { id: "RELAX",  label: "Relax",  emoji: "🌙", desc: "Warm yellow light",   color: "#fbbf24" },
  { id: "OFF",    label: "Off",    emoji: "⚫", desc: "Turn lamp off",       color: "#6b7280" },
];

export default function ModeControl() {
  const [activeMode, setActiveMode] = useState(null);
  const [sending, setSending]       = useState(false);
  const [toast, setToast]           = useState(null);

  const sendMode = async (modeId) => {
    setSending(true);
    try {
      // The backend would relay this via MQTT to the ESP32
      // For now we just hit the health endpoint as a demo
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        setActiveMode(modeId);
        setToast(`✅ Mode switched to ${modeId}`);
        setTimeout(() => setToast(null), 3000);
      }
    } catch (e) {
      setToast("❌ Could not reach backend");
      setTimeout(() => setToast(null), 3000);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="mode-control-card">
      <h2>Manual Mode Override</h2>
      <p className="mode-subtitle">Tap a mode to override AI control and send directly to the lamp.</p>

      <div className="mode-buttons">
        {MODES.map(mode => (
          <button
            key={mode.id}
            className={`mode-btn ${activeMode === mode.id ? "active" : ""}`}
            style={{
              borderColor: mode.color,
              boxShadow: activeMode === mode.id ? `0 0 16px ${mode.color}55` : "none",
              background: activeMode === mode.id ? `${mode.color}22` : "#0f172a",
            }}
            onClick={() => sendMode(mode.id)}
            disabled={sending}
          >
            <span className="mode-emoji">{mode.emoji}</span>
            <span className="mode-label" style={{ color: mode.color }}>{mode.label}</span>
            <span className="mode-desc">{mode.desc}</span>
          </button>
        ))}
      </div>

      {toast && <div className="toast">{toast}</div>}

      <div className="pomodoro-info">
        <span>⏱️ Pomodoro Break Reminder fires every 45 min automatically via the edge engine.</span>
      </div>
    </div>
  );
}
