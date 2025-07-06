import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TimeSeries } from "@/types/api";
import { Users } from "lucide-react";
import SpeedMeter from "./SpeedMeter";

interface CurrentCongestionCardProps {
  timeSeries: TimeSeries[] | null;
  selectedPlaceName: string;
  loading: boolean;
  error: Error | null;
}

const CurrentCongestionCard = ({
  timeSeries: timeSeries,
  selectedPlaceName,
  loading,
  error,
}: CurrentCongestionCardProps) => {
  const getCurrentCongestion = () => {
    if (!timeSeries) return undefined;
    const latestActual = timeSeries
      .filter((d) => d.actualScore !== undefined)
      .slice(-1)[0];
    return latestActual?.actualScore;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Users className="w-5 h-5 mr-2" />
          現在の混雑度 - {selectedPlaceName}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex justify-center h-32">
        {loading ? (
          <div className="flex justify-center items-center">
            <div className="text-gray-500">読み込み中...</div>
          </div>
        ) : error ? (
          <div className="flex justify-center items-center">
            <div className="text-red-500">エラー: {error.message}</div>
          </div>
        ) : (
          <SpeedMeter value={getCurrentCongestion()} />
        )}
      </CardContent>
    </Card>
  );
};

export default CurrentCongestionCard;
