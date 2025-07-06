import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { TimeSeries } from "@/types/api";
import { ChartLine } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts";

interface ChartCardProps {
  timeSeries: TimeSeries[] | null;
  loading: boolean;
  error: Error | null;
  currentTimestamp: number;
}

const chartConfig = {
  actual: {
    label: "実測値",
    color: "#3b82f6",
  },
  predicted: {
    label: "予測値",
    color: "#f59e0b",
  },
};

const smoothPredictedData = (
  data: Array<{
    time: number;
    actual: number | null;
    predicted: number | null;
  }>
) => {
  const smoothedData = [...data];
  const windowSize = 1;

  for (let i = 0; i < smoothedData.length; i++) {
    if (smoothedData[i].predicted !== null) {
      const start = Math.max(0, i - Math.floor(windowSize / 2));
      const end = Math.min(
        smoothedData.length,
        i + Math.floor(windowSize / 2) + 1
      );

      const validValues = smoothedData
        .slice(start, end)
        .map((item) => item.predicted)
        .filter((val) => val !== null) as number[];

      if (validValues.length > 0) {
        const average =
          validValues.reduce((sum, val) => sum + val, 0) / validValues.length;
        smoothedData[i] = {
          ...smoothedData[i],
          predicted: Math.round(average),
        };
      }
    }
  }

  return smoothedData;
};

const ChartCard = ({
  timeSeries,
  loading,
  error,
  currentTimestamp,
}: ChartCardProps) => {
  const timeSeriesData = timeSeries?.length
    ? smoothPredictedData(
        timeSeries.map((t) => ({
          time: t.timestamp.getTime(),
          actual: t.actualScore || null,
          predicted: t.predictedScore || null,
        }))
      )
    : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <ChartLine className="w-5 h-5 mr-2" />
          混雑度の推移
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center items-center h-96">
            <div className="text-gray-500">読み込み中...</div>
          </div>
        ) : error ? (
          <div className="flex justify-center items-center h-96">
            <div className="text-red-500">エラー: {error.message}</div>
          </div>
        ) : (
          <>
            <div className="mb-4 flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-gray-600">実測値</span>
              </div>
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 bg-yellow-500 rounded-full border-2 border-yellow-500"
                  style={{
                    backgroundImage:
                      "repeating-linear-gradient(45deg, transparent, transparent 2px, white 2px, white 4px)",
                  }}
                ></div>
                <span className="text-sm text-gray-600">予測値</span>
              </div>
            </div>
            <div className="w-full">
              <ChartContainer config={chartConfig} className="h-96 w-full">
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="time"
                    tickLine={false}
                    axisLine={false}
                    className="text-xs"
                    type="number"
                    scale="time"
                    domain={["dataMin", "dataMax"]}
                    ticks={Array.from({ length: 24 }, (_, i) => {
                      const startOfDay = new Date();
                      startOfDay.setHours(0, 0, 0, 0);
                      return startOfDay.getTime() + i * 60 * 60 * 1000;
                    })}
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return date.getHours() + ":00";
                    }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    className="text-xs"
                    domain={[0, 120]}
                    tick={false}
                    width={10}
                  />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <ReferenceLine
                    x={currentTimestamp}
                    stroke="#6b7280"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                  />
                  <ReferenceLine
                    y={100}
                    stroke="#ef4444"
                    strokeWidth={1}
                    strokeDasharray="4 4"
                  />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="var(--color-actual)"
                    strokeWidth={3}
                    dot={{
                      fill: "var(--color-actual)",
                      strokeWidth: 0,
                      r: 4,
                    }}
                    connectNulls={true}
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="var(--color-predicted)"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={{
                      fill: "var(--color-predicted)",
                      strokeWidth: 0,
                      r: 4,
                    }}
                    connectNulls={true}
                  />
                </LineChart>
              </ChartContainer>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default ChartCard;
