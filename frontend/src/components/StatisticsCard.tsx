import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Place, TimeSeries } from "@/types/api";
import { FileSpreadsheet } from "lucide-react";

interface StatisticsCardProps {
  timeSeries: TimeSeries[] | null;
  place: Place | null;
  loading: boolean;
  error: Error | null;
}

const StatisticsCard = ({
  timeSeries,
  place,
  loading,
  error,
}: StatisticsCardProps) => {
  const isOpen = (timestamp: Date) => {
    if (!place?.opens) return false;
    const dayOfWeek = timestamp.getDay();
    const currentTime =
      timestamp.getHours() * 60 * 60 * 1000 +
      timestamp.getMinutes() * 60 * 1000;
    const todayHours = place.opens[dayOfWeek];
    if (!todayHours) return false;
    return todayHours.some(([start, end]) => {
      return currentTime >= start && currentTime <= end;
    });
  };

  const getFutureOpenPeak = () => {
    if (!timeSeries || !place?.opens) return { score: 0, time: null };

    const now = new Date();
    const futureOpenTimeSeries = timeSeries
      .filter((t) => t.targetDatetime >= now && isOpen(t.targetDatetime))
      .filter((t) => t.predictedScore !== undefined && t.predictedScore > 0);

    if (futureOpenTimeSeries.length === 0) return { score: 0, time: null };

    const peak = futureOpenTimeSeries.reduce((max, current) => {
      return (current.predictedScore || 0) > (max.predictedScore || 0)
        ? current
        : max;
    });

    return {
      score: peak.predictedScore
        ? Math.round(peak.predictedScore * 10) / 10
        : undefined,
      time: peak.targetDatetime,
    };
  };

  const getTodaysPeak = () => {
    if (!timeSeries) return { score: 0, time: null };

    const today = new Date();
    const startOfDay = new Date(today);
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(today);
    endOfDay.setHours(23, 59, 59, 999);

    const todayData = timeSeries
      .filter(
        (t) => t.targetDatetime >= startOfDay && t.targetDatetime <= endOfDay
      )
      .filter((t) => t.actualScore !== undefined);

    if (todayData.length === 0) return { score: 0, time: null };

    const peak = todayData.reduce((max, current) => {
      return (current.actualScore || 0) > (max.actualScore || 0)
        ? current
        : max;
    });

    return {
      score: peak.predictedScore
        ? Math.round(peak.predictedScore * 10) / 10
        : undefined,
      time: peak.targetDatetime,
    };
  };

  const getAverageCongestion = () => {
    if (!timeSeries) return 0;
    const actualScores = timeSeries
      .map((t) => t.actualScore)
      .filter((score) => score !== undefined) as number[];

    if (actualScores.length === 0) return 0;

    const total = actualScores.reduce((sum, score) => sum + score, 0);
    return Math.round((total / actualScores.length) * 10) / 10;
  };

  const formatTime = (timestamp: Date | null) => {
    if (!timestamp) return "";
    return timestamp.toLocaleTimeString("ja-JP", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getCongestionColor = (value: number | undefined) => {
    if (value === undefined) return "#dc2626";
    if (value <= 30) return "#22c55e";
    if (value <= 60) return "#f59e0b";
    if (value <= 80) return "#f97316";
    if (value <= 100) return "#ef4444";
    return "#dc2626";
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <FileSpreadsheet className="w-5 h-5 mr-2" />
          統計情報
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center items-center h-32">
            <div className="text-gray-500">読み込み中...</div>
          </div>
        ) : error ? (
          <div className="flex justify-center items-center h-32">
            <div className="text-red-500">エラー: {error.message}</div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">今後のピーク時間</span>
              <div>
                {getFutureOpenPeak().time ? (
                  <>
                    <span className="text-xl font-bold">
                      {formatTime(getFutureOpenPeak().time)}
                    </span>
                    <div
                      className="text-xs text-gray-400"
                      style={{
                        color: getCongestionColor(getFutureOpenPeak().score),
                      }}
                    >
                      {(getFutureOpenPeak().score || 0) + "%"}
                    </div>
                  </>
                ) : (
                  <span className="text-sm text-gray-500">営業終了</span>
                )}
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">今日のピーク時間</span>
              <div>
                <span className="text-xl font-bold">
                  {formatTime(getTodaysPeak().time)}
                </span>
                <div
                  className="text-xs text-gray-400"
                  style={{ color: getCongestionColor(getTodaysPeak().score) }}
                >
                  {getTodaysPeak().score}%
                </div>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">今日の平均混雑度</span>
              <span
                className="text-xl font-bold"
                style={{
                  color: getCongestionColor(Number(getAverageCongestion())),
                }}
              >
                {getAverageCongestion()}%
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default StatisticsCard;
