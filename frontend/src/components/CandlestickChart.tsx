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
} from "recharts";
import type { TechnicalData } from "../types";

interface CandlestickChartProps {
  data: TechnicalData[];
}

interface CandleBarData {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  body: [number, number];
  wick: [number, number];
  fill: string;
  sma_5: number | null;
  sma_25: number | null;
  sma_75: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
}

export default function CandlestickChart({ data }: CandlestickChartProps) {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-8">データがありません。</p>;
  }

  const chartData: CandleBarData[] = data
    .filter((d) => d.open != null && d.close != null && d.high != null && d.low != null)
    .map((d) => {
      const isUp = (d.close ?? 0) >= (d.open ?? 0);
      return {
        date: d.date,
        open: d.open!,
        close: d.close!,
        high: d.high!,
        low: d.low!,
        body: isUp ? [d.open!, d.close!] : [d.close!, d.open!],
        wick: [d.low!, d.high!],
        fill: isUp ? "#ef4444" : "#3b82f6",
        sma_5: d.sma_5,
        sma_25: d.sma_25,
        sma_75: d.sma_75,
        bb_upper: d.bb_upper,
        bb_middle: d.bb_middle,
        bb_lower: d.bb_lower,
      };
    });

  const allPrices = chartData.flatMap((d) => [d.high, d.low]);
  const minPrice = Math.floor(Math.min(...allPrices) * 0.98);
  const maxPrice = Math.ceil(Math.max(...allPrices) * 1.02);

  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">株価チャート</h3>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            tickFormatter={(v: string) => v.slice(5)}
            interval={Math.floor(chartData.length / 8)}
          />
          <YAxis domain={[minPrice, maxPrice]} tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(value, name) => {
              if (Array.isArray(value)) return null;
              if (typeof value === "number") return [value.toLocaleString(), name];
              return null;
            }}
            labelFormatter={(label) => `日付: ${label}`}
          />
          <Legend />
          {/* ヒゲ（高値-安値） */}
          <Bar dataKey="wick" fill="#9ca3af" barSize={1} isAnimationActive={false} legendType="none" />
          {/* 実体（始値-終値） */}
          <Bar
            dataKey="body"
            barSize={6}
            isAnimationActive={false}
            legendType="none"
            shape={(props) => {
              const { x, y, width, height, payload } = props as unknown as {
                x: number; y: number; width: number; height: number; payload: CandleBarData;
              };
              return <rect x={x} y={y} width={width} height={Math.max(height, 1)} fill={payload?.fill ?? "#9ca3af"} />;
            }}
          />
          {/* 移動平均線 */}
          <Line type="monotone" dataKey="sma_5" stroke="#f59e0b" dot={false} strokeWidth={1} name="SMA5" />
          <Line type="monotone" dataKey="sma_25" stroke="#10b981" dot={false} strokeWidth={1} name="SMA25" />
          <Line type="monotone" dataKey="sma_75" stroke="#8b5cf6" dot={false} strokeWidth={1} name="SMA75" />
          {/* ボリンジャーバンド */}
          <Line
            type="monotone"
            dataKey="bb_upper"
            stroke="#94a3b8"
            dot={false}
            strokeWidth={1}
            strokeDasharray="4 4"
            name="BB上限"
          />
          <Line
            type="monotone"
            dataKey="bb_lower"
            stroke="#94a3b8"
            dot={false}
            strokeWidth={1}
            strokeDasharray="4 4"
            name="BB下限"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
