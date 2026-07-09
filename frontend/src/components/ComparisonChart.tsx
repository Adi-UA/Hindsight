import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { StrategyResult } from "../api";

// Distinct colors for up to three strategy equity lines.
const COLORS = ["#3b82f6", "#f59e0b", "#a855f7"];

export function ComparisonChart({ results }: { results: StrategyResult[] }) {
  if (results.length === 0) return null;

  // All strategies ran over the same data, so their series share dates.
  const base = results[0].series;
  const data = base.map((point, i) => {
    const row: Record<string, number | string> = {
      date: point.date,
      close: point.close,
    };
    results.forEach((r) => {
      row[r.strategy] = r.series[i]?.equity ?? Number.NaN;
    });
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#a0aec0" }} minTickGap={40} />
        <YAxis
          yAxisId="equity"
          width={72}
          tick={{ fontSize: 11, fill: "#a0aec0" }}
          tickFormatter={(v: number) => `$${Math.round(v / 1000)}k`}
        />
        <YAxis
          yAxisId="price"
          orientation="right"
          width={60}
          tick={{ fontSize: 11, fill: "#a0aec0" }}
        />
        <Tooltip contentStyle={{ background: "#1a202c", border: "1px solid #2d3748" }} />
        <Legend />
        <Line
          yAxisId="price"
          type="monotone"
          dataKey="close"
          name="Price"
          stroke="#718096"
          strokeWidth={1}
          dot={false}
        />
        {results.map((r, i) => (
          <Line
            key={r.strategy}
            yAxisId="equity"
            type="monotone"
            dataKey={r.strategy}
            name={r.strategy}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
