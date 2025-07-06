import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TimeSeries } from "@/types/api";
import { FileSpreadsheet, TrendingUp } from "lucide-react";

interface StatisticsCardProps {
  timeSeries: TimeSeries[] | null;
  loading: boolean;
  error: Error | null;
}

const StatisticsCard = ({
  timeSeries,
  loading,
  error,
}: StatisticsCardProps) => {
  const getCurrentCongestion = () => {
    if (!timeSeries) return 0;
    const latestActual = timeSeries
      .filter((t) => t.actualScore !== undefined)
      .slice(-1)[0];
    return latestActual?.actualScore || 0;
  };

  const getMaxCongestion = () => {
    if (!timeSeries) return 0;
    return Math.max(...timeSeries.map((t) => t.actualScore || 0));
  };

  const getAverageCongestion = () => {
    if (!timeSeries) return 0;
    const total = timeSeries.reduce((sum, t) => sum + (t.actualScore || 0), 0);
    return (total / timeSeries.length).toFixed(1);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            統計情報
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center items-center h-32">
            <div className="text-gray-500">読み込み中...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            統計情報
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center items-center h-32">
            <div className="text-red-500">エラー: {error.message}</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <FileSpreadsheet className="w-5 h-5 mr-2" />
          統計情報
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4 h-32">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">現在の混雑度</span>
            <span className="text-2xl font-bold text-gray-900">
              {getCurrentCongestion()}%
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">今日の最高混雑度</span>
            <span className="text-lg font-semibold text-red-600">
              {getMaxCongestion()}%
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">平均混雑度</span>
            <span className="text-lg font-semibold text-blue-600">
              {getAverageCongestion()}%
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default StatisticsCard;
