import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Marker, SeriesPoint } from "../api";

export function EquityChart({
  series,
  markers,
}: {
  series: SeriesPoint[];
  markers: Marker[];
}) {
  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={series} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#a0aec0" }} minTickGap={40} />
        <YAxis
          yAxisId="equity"
          width={70}
          tick={{ fontSize: 11, fill: "#a0aec0" }}
          tickFormatter={(v: number) => `$${Math.round(v / 1000)}k`}
        />
        <YAxis
          yAxisId="price"
          orientation="right"
          width={60}
          tick={{ fontSize: 11, fill: "#a0aec0" }}
        />
        <Tooltip
          contentStyle={{ background: "#1a202c", border: "1px solid #2d3748" }}
        />
        <Legend />
        <Line
          yAxisId="equity"
          type="monotone"
          dataKey="equity"
          name="Equity"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
        />
        <Line
          yAxisId="price"
          type="monotone"
          dataKey="close"
          name="Price"
          stroke="#a0aec0"
          strokeWidth={1}
          dot={false}
        />
        {markers.map((m, i) => (
          <ReferenceDot
            key={`${m.date}-${i}`}
            x={m.date}
            y={m.price}
            yAxisId="price"
            r={4}
            fill={m.side === "BUY" ? "#22c55e" : "#ef4444"}
            stroke="none"
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
