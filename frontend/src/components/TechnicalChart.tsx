import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from "recharts";
import type { TechnicalData } from "../types";

interface TechnicalChartProps {
  data: TechnicalData[];
}

export default function TechnicalChart({ data }: TechnicalChartProps) {
  if (data.length === 0) {
    return null;
  }

  const tickInterval = Math.floor(data.length / 8);

  return (
    <div className="space-y-6">
      {/* RSI */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">RSI (14)</h3>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: string) => v.slice(5)}
              interval={tickInterval}
            />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
            <Tooltip labelFormatter={(label) => `日付: ${label}`} />
            <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" label="70" />
            <ReferenceLine y={30} stroke="#3b82f6" strokeDasharray="3 3" label="30" />
            <Line type="monotone" dataKey="rsi_14" stroke="#8b5cf6" dot={false} strokeWidth={1.5} name="RSI" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* MACD */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">MACD (12/26/9)</h3>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: string) => v.slice(5)}
              interval={tickInterval}
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip labelFormatter={(label) => `日付: ${label}`} />
            <Legend />
            <ReferenceLine y={0} stroke="#9ca3af" />
            <Bar
              dataKey="macd_histogram"
              fill="#94a3b8"
              name="ヒストグラム"
              isAnimationActive={false}
              barSize={3}
            />
            <Line type="monotone" dataKey="macd" stroke="#3b82f6" dot={false} strokeWidth={1.5} name="MACD" />
            <Line
              type="monotone"
              dataKey="macd_signal"
              stroke="#ef4444"
              dot={false}
              strokeWidth={1.5}
              name="シグナル"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
