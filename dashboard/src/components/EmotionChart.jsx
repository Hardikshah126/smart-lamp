// components/EmotionChart.jsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export function EmotionChart({ data }) {
  if (!data || data.length === 0) {
    return <div className="chart-empty">No mood data yet.</div>;
  }

  // Count occurrences of each emotion
  const counts = { happy: 0, stressed: 0, sleepy: 0, unknown: 0 };
  data.forEach(d => {
    if (d.emotion in counts) counts[d.emotion]++;
  });

  const chartData = [
    { name: "😊 Happy",   count: counts.happy,    color: "#22c55e" },
    { name: "😰 Stressed", count: counts.stressed, color: "#a78bfa" },
    { name: "😴 Sleepy",  count: counts.sleepy,   color: "#fbbf24" },
  ];

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <Tooltip
          contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
          labelStyle={{ color: "#e2e8f0" }}
          itemStyle={{ color: "#94a3b8" }}
        />
        <Bar dataKey="count" radius={[6, 6, 0, 0]} name="Detections">
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export default EmotionChart;
