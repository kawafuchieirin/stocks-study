import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { TechnicalData } from "../types";

interface VolumeChartProps {
  data: TechnicalData[];
}

interface VolumeBarData {
  date: string;
  volume: number;
  fill: string;
}

/**
 * 出来高を表示するバーチャート。
 * 陽線（終値>=始値）は赤、陰線は青で色分けする。
 */
export default function VolumeChart({ data }: VolumeChartProps) {
  if (data.length === 0) {
    return null;
  }

  const chartData: VolumeBarData[] = data
    .filter((d) => d.volume != null)
    .map((d) => {
      const isUp = (d.close ?? 0) >= (d.open ?? 0);
      return {
        date: d.date,
        volume: d.volume!,
        fill: isUp ? "#ef4444" : "#3b82f6",
      };
    });

  if (chartData.length === 0) {
    return null;
  }

  const tickInterval = Math.floor(chartData.length / 8);

  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">出来高</h3>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart
          data={chartData}
          margin={{ top: 5, right: 20, bottom: 5, left: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            tickFormatter={(v: string) => v.slice(5)}
            interval={tickInterval}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) => {
              if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
              if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
              return String(v);
            }}
          />
          <Tooltip
            formatter={(value) => {
              if (typeof value === "number") return [value.toLocaleString(), "出来高"];
              return null;
            }}
            labelFormatter={(label) => `日付: ${label}`}
          />
          <Bar
            dataKey="volume"
            isAnimationActive={false}
            barSize={4}
            shape={(props) => {
              const { x, y, width, height, payload } = props as unknown as {
                x: number;
                y: number;
                width: number;
                height: number;
                payload: VolumeBarData;
              };
              return (
                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={Math.max(height, 0)}
                  fill={payload?.fill ?? "#9ca3af"}
                />
              );
            }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
