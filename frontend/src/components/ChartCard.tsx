import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Place, TimeSeries } from "@/types/api";
import { ChartLine } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts";

interface ChartCardProps {
  timeSeries: TimeSeries[] | null;
  place: Place | null;
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
  const windowSize = 3;

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
  place,
  loading,
  error,
  currentTimestamp,
}: ChartCardProps) => {
  const getTimeRange = () => {
    if (!place?.range) {
      return { minHour: 9, maxHour: 21 };
    }
    return { minHour: place.range[0], maxHour: place.range[1] };
  };

  const { minHour, maxHour } = getTimeRange();

  const timeSeriesData = timeSeries?.length
    ? smoothPredictedData(
        timeSeries
          .map((t) => ({
            time: t.targetDatetime.getTime(),
            actual: t.actualScore || null,
            predicted: t.predictedScore || null,
          }))
          .filter((item) => {
            const hour = new Date(item.time).getHours();
            return hour >= minHour && hour <= maxHour;
          })
      )
    : [];

  const getMaxValue = () => {
    const allValues = timeSeriesData
      .flatMap((t) => [t.actual, t.predicted])
      .filter((v) => v !== null) as number[];
    return allValues.length > 0 ? Math.max(...allValues) : 0;
  };

  const yAxisMax = Math.max(120, getMaxValue() + 10);

  const startOfDay = new Date();
  startOfDay.setHours(0, 0, 0, 0);

  const getOpenAreas = () => {
    if (!place?.opens) return [];
    const areas: { x1: number; x2: number }[] = [];
    const today = new Date();
    const startOfDay = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
      0,
      0,
      0,
      0
    );
    place.opens[new Date().getDay()].forEach(([start, end]) => {
      areas.push({
        x1: startOfDay.getTime() + start,
        x2: startOfDay.getTime() + end,
      });
    });
    return areas;
  };
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
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full opacity-30"></div>
                <span className="text-sm text-gray-600">営業時間</span>
              </div>
            </div>
            <div className="w-full">
              <ChartContainer config={chartConfig} className="h-96 w-full">
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  {getOpenAreas().map((area, index) => (
                    <ReferenceArea
                      key={index}
                      x1={area.x1}
                      x2={area.x2}
                      fill="#10b981"
                      fillOpacity={0.1}
                    />
                  ))}
                  <XAxis
                    dataKey="time"
                    tickLine={false}
                    axisLine={false}
                    className="text-xs"
                    type="number"
                    scale="time"
                    domain={[
                      startOfDay.getTime() + minHour * 60 * 60 * 1000,
                      startOfDay.getTime() + maxHour * 60 * 60 * 1000,
                    ]}
                    ticks={Array.from(
                      { length: maxHour - minHour + 1 },
                      (_, i) => {
                        return (
                          startOfDay.getTime() + (minHour + i) * 60 * 60 * 1000
                        );
                      }
                    )}
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return date.getHours() + ":00";
                    }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    className="text-xs"
                    domain={[0, yAxisMax]}
                    tick={false}
                    width={10}
                  />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <ReferenceLine
                    x={currentTimestamp}
                    stroke="#6b7280"
                    strokeWidth={3}
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
