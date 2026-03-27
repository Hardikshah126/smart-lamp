// components/EnergyChart.jsx
// Line chart showing energy consumption + temperature over time

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

export default function EnergyChart({ data }) {
  if (!data || data.length === 0) {
    return <div className="chart-empty">No energy data available yet.</div>;
  }

  const formatted = data
    .filter(d => d.energy_kwh != null)
    .map(d => ({
      time: d.created_at
        ? new Date(d.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        : "--",
      energy_wh: parseFloat((d.energy_kwh * 1000).toFixed(3)),
      temperature: d.temperature != null ? parseFloat(d.temperature.toFixed(1)) : null,
      ldr: d.ldr != null ? parseFloat(d.ldr.toFixed(0)) : null,
    }))
    .reverse();   // oldest first

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={formatted} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="time"
          tick={{ fill: "#94a3b8", fontSize: 11 }}
          interval="preserveStartEnd"
        />
        <YAxis
          yAxisId="energy"
          tick={{ fill: "#94a3b8", fontSize: 11 }}
          label={{ value: "Wh", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }}
        />
        <YAxis
          yAxisId="temp"
          orientation="right"
          tick={{ fill: "#94a3b8", fontSize: 11 }}
          label={{ value: "°C", angle: 90, position: "insideRight", fill: "#94a3b8", fontSize: 11 }}
        />
        <Tooltip
          contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
          labelStyle={{ color: "#e2e8f0" }}
          itemStyle={{ color: "#94a3b8" }}
        />
        <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
        <Line
          yAxisId="energy"
          type="monotone"
          dataKey="energy_wh"
          stroke="#fb923c"
          strokeWidth={2}
          dot={false}
          name="Energy (Wh)"
        />
        <Line
          yAxisId="temp"
          type="monotone"
          dataKey="temperature"
          stroke="#ef4444"
          strokeWidth={1.5}
          dot={false}
          strokeDasharray="4 2"
          name="Temp (°C)"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
