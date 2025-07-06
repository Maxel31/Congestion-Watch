import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Place, TimeSeries } from "@/types/api";
import { Users } from "lucide-react";
import SpeedMeter from "./SpeedMeter";

interface CurrentStatusCardProps {
  timeSeries: TimeSeries[] | null;
  place: Place | null;
  loading: boolean;
  error: Error | null;
}

const CurrentStatusCard = ({
  timeSeries,
  place,
  loading,
  error,
}: CurrentStatusCardProps) => {
  const getCurrentCongestion = () => {
    if (!timeSeries) return undefined;
    const latestActual = timeSeries
      .filter((d) => d.actualScore !== undefined)
      .slice(-1)[0];
    return latestActual?.actualScore;
  };

  const isCurrentlyOpen = () => {
    if (!place?.opens) return false;

    const now = new Date();
    const dayOfWeek = now.getDay();
    const currentTime =
      now.getHours() * 60 * 60 * 1000 + now.getMinutes() * 60 * 1000;

    const todayHours = place.opens[dayOfWeek];
    if (!todayHours) return false;

    return todayHours.some(([start, end]) => {
      return currentTime >= start && currentTime <= end;
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            <Users className="w-5 h-5 mr-2" />
            現在の混雑度 - {place ? place.name : "選択してください"}
          </div>
          {place && (
            <span
              className={`text-sm px-2 py-1 rounded-full ${
                isCurrentlyOpen()
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              }`}
            >
              {isCurrentlyOpen() ? "営業中" : "営業外"}
            </span>
          )}
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
          <>
            <SpeedMeter value={getCurrentCongestion()} />
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default CurrentStatusCard;
