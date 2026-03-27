// components/StatusCards.jsx
// Top row of stat cards — emotion, mode, temperature, energy

export default function StatusCards({ summary }) {
  if (!summary) return null;

  const EMOTION_EMOJI = { happy: "😊", stressed: "😰", sleepy: "😴", unknown: "🤔" };
  const MODE_COLOR    = { FOCUS: "#60a5fa", CALM: "#a78bfa", RELAX: "#fbbf24", AUTO: "#9ca3af" };
  const EMOTION_BG    = { happy: "#052e16", stressed: "#1e1b4b", sleepy: "#451a03", unknown: "#1f2937" };

  const cards = [
    {
      label: "Current Emotion",
      value: summary.current_emotion.toUpperCase(),
      sub: `${EMOTION_EMOJI[summary.current_emotion] || "🤔"} Detected via camera`,
      accent: "#a78bfa",
      bg: EMOTION_BG[summary.current_emotion] || "#1f2937",
    },
    {
      label: "Lighting Mode",
      value: summary.current_mode,
      sub: "Auto-adjusted by AI",
      accent: MODE_COLOR[summary.current_mode] || "#9ca3af",
      bg: "#0f172a",
    },
    {
      label: "Temperature",
      value: summary.temperature != null ? `${summary.temperature.toFixed(1)}°C` : "--",
      sub: summary.temperature > 40 ? "⚠️ High — check device" : "✅ Normal range",
      accent: summary.temperature > 40 ? "#ef4444" : "#22c55e",
      bg: "#0f172a",
    },
    {
      label: "Humidity",
      value: summary.humidity != null ? `${summary.humidity.toFixed(0)}%` : "--",
      sub: "DHT11 sensor",
      accent: "#38bdf8",
      bg: "#0f172a",
    },
    {
      label: "Energy Used",
      value: summary.total_energy_kwh != null
        ? `${(summary.total_energy_kwh * 1000).toFixed(1)} Wh`
        : "--",
      sub: "Session consumption",
      accent: "#fb923c",
      bg: "#0f172a",
    },
    {
      label: "Ambient Light",
      value: summary.ldr != null ? `${Math.round(summary.ldr)} lux` : "--",
      sub: "LDR sensor reading",
      accent: "#facc15",
      bg: "#0f172a",
    },
  ];

  return (
    <div className="status-cards">
      {cards.map((card, i) => (
        <div
          key={i}
          className="status-card"
          style={{ background: card.bg, borderTop: `3px solid ${card.accent}` }}
        >
          <p className="card-label">{card.label}</p>
          <p className="card-value" style={{ color: card.accent }}>{card.value}</p>
          <p className="card-sub">{card.sub}</p>
        </div>
      ))}
    </div>
  );
}
