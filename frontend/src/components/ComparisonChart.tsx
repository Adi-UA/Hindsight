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

import type { SymbolResult } from "../api";

// Distinct colors for up to three symbol equity lines.
const COLORS = ["#3b82f6", "#f59e0b", "#a855f7"];

// Compact currency for axis ticks, e.g. $1.5K, $2.5K, $1M (no duplicate labels).
const AXIS_FMT = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});

export function ComparisonChart({ results }: { results: SymbolResult[] }) {
  if (results.length === 0) return null;

  // Same strategy, same date range, so equity curves share dates and all start
  // at the same cash, which makes them directly comparable.
  const base = results[0].series;
  const data = base.map((point, i) => {
    const row: Record<string, number | string> = { date: point.date };
    results.forEach((r) => {
      row[r.symbol] = r.series[i]?.equity ?? Number.NaN;
    });
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#a0aec0" }} minTickGap={40} />
        <YAxis
          width={72}
          tick={{ fontSize: 11, fill: "#a0aec0" }}
          tickFormatter={(v: number) => AXIS_FMT.format(v)}
        />
        <Tooltip contentStyle={{ background: "#1a202c", border: "1px solid #2d3748" }} />
        <Legend />
        {results.map((r, i) => (
          <Line
            key={r.symbol}
            type="monotone"
            dataKey={r.symbol}
            name={r.symbol}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
