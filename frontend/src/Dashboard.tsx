import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { usePlaceDetail, usePlaces } from "@/hooks/usePlaces";
import { usePolling } from "@/hooks/usePolling";
import { Clock, MapPin, TrendingUp, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";

const Dashboard = () => {
  const [selectedPlaceId, setSelectedPlaceId] = useState<number | null>(null);
  const {
    places,
    loading: placesLoading,
    error: placesError,
    refetch: refreshPlaces,
  } = usePlaces();
  const {
    placeDetail,
    loading: placeDetailLoading,
    error: placeDetailError,
    refetch: refreshPlaceDetail,
  } = usePlaceDetail(selectedPlaceId || 0);

  const refreshInterval = parseInt(
    import.meta.env.VITE_REFRESH_INTERVAL || "30000",
    10
  );
  usePolling(
    () => {
      refreshPlaces();
      if (selectedPlaceId) {
        refreshPlaceDetail();
      }
    },
    { interval: refreshInterval }
  );

  const selectedPlace = places.find((f) => f.id === selectedPlaceId);

  const timeSeriesData =
    placeDetail?.timeSeries.map((item) => ({
      time: new Date(item.timestamp).toLocaleTimeString("ja-JP", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      actual: item.actualScore || null,
      predicted: item.predictedScore || null,
      hour: new Date(item.timestamp).getHours(),
    })) || [];

  const getCrowdnessInfo = (value: number) => {
    if (value <= 30)
      return { color: "#22c55e", label: "空いている", bgColor: "bg-green-100" };
    if (value <= 60)
      return { color: "#f59e0b", label: "普通", bgColor: "bg-yellow-100" };
    if (value <= 80)
      return { color: "#f97316", label: "混雑", bgColor: "bg-orange-100" };
    return { color: "#ef4444", label: "非常に混雑", bgColor: "bg-red-100" };
  };

  // スピードメータコンポーネント
  const SpeedMeter = ({
    value,
    size = 200,
  }: {
    value: number;
    size?: number;
  }) => {
    const center = size / 2;
    const radius = size / 2 - 20;
    const circumference = Math.PI * radius;
    const strokeDasharray = circumference;
    const strokeDashoffset = circumference - (value / 100) * circumference;

    const { color, label } = getCrowdnessInfo(value);

    return (
      <div className="flex flex-col items-center">
        <div
          className="relative"
          style={{ width: size, height: size / 2 + 40 }}
        >
          <svg
            width={size}
            height={size / 2 + 40}
            className="transform rotate-180"
            style={{ overflow: "visible" }}
          >
            {/* 背景の円弧 */}
            <path
              d={`M 20 ${center} A ${radius} ${radius} 0 0 1 ${
                size - 20
              } ${center}`}
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="8"
              strokeLinecap="round"
            />
            {/* 進捗の円弧 */}
            <path
              d={`M 20 ${center} A ${radius} ${radius} 0 0 1 ${
                size - 20
              } ${center}`}
              fill="none"
              stroke={color}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-1000 ease-out"
            />
            {/* 目盛り */}
            {[0, 25, 50, 75, 100].map((tick) => {
              const angle = (tick / 100) * Math.PI;
              const x1 = center + (radius - 10) * Math.cos(angle);
              const y1 = center - (radius - 10) * Math.sin(angle);
              const x2 = center + (radius - 20) * Math.cos(angle);
              const y2 = center - (radius - 20) * Math.sin(angle);

              return (
                <line
                  key={tick}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="#9ca3af"
                  strokeWidth="2"
                />
              );
            })}
          </svg>
          {/* 中央の数値 */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-4xl font-bold text-gray-800 mt-8">
              {value}%
            </div>
            <div className="text-sm text-gray-600 mt-1">{label}</div>
          </div>
        </div>
      </div>
    );
  };

  // チャート設定
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

  // 現在時刻の表示
  const currentTime = new Date().toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
  });

  useEffect(() => {
    // 初期選択: 最初の施設を選択
    if (places.length > 0 && selectedPlaceId === null) {
      setSelectedPlaceId(places[0].id);
    }
  }, [places, selectedPlaceId]);

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* ヘッダー */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              施設混雑度モニター
            </h1>
            <p className="text-gray-600 mt-1">
              リアルタイムの混雑状況と予測を表示
            </p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>最終更新: {currentTime}</span>
          </div>
        </div>

        {/* 施設選択 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <MapPin className="w-5 h-5 mr-2" />
              施設選択
            </CardTitle>
          </CardHeader>
          <CardContent>
            {placesLoading ? (
              <div className="flex justify-center items-center h-32">
                <div className="text-gray-500">読み込み中...</div>
              </div>
            ) : placesError ? (
              <div className="flex justify-center items-center h-32">
                <div className="text-red-500">
                  エラー: {placesError.message}
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {places.map((place) => {
                  return (
                    <button
                      key={place.id}
                      onClick={() => setSelectedPlaceId(place.id)}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        selectedPlaceId === place.id
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-gray-900">
                          {place.name}
                        </h3>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* メインダッシュボード */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 現在の混雑度 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Users className="w-5 h-5 mr-2" />
                現在の混雑度 - {selectedPlace?.name || "選択してください"}
              </CardTitle>
              <CardDescription>リアルタイムの混雑状況</CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
              {placeDetailLoading ? (
                <div className="flex justify-center items-center h-64">
                  <div className="text-gray-500">読み込み中...</div>
                </div>
              ) : placeDetailError ? (
                <div className="flex justify-center items-center h-64">
                  <div className="text-red-500">
                    エラー: {placeDetailError.message}
                  </div>
                </div>
              ) : (
                <SpeedMeter value={30} size={250} />
              )}
            </CardContent>
          </Card>

          {/* 統計情報 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                統計情報
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">現在の混雑度</span>
                  <span className="text-2xl font-bold text-gray-900">
                    {30}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">
                    今日の最高混雑度
                  </span>
                  <span className="text-lg font-semibold text-red-600">
                    {placeDetail
                      ? Math.max(
                          ...placeDetail.timeSeries.map(
                            (d) => d.actualScore || 0
                          )
                        )
                      : 0}
                    %
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">平均混雑度</span>
                  <span className="text-lg font-semibold text-blue-600">
                    {placeDetail
                      ? (
                          placeDetail.timeSeries.reduce(
                            (sum, d) => sum + (d.actualScore || 0),
                            0
                          ) / placeDetail.timeSeries.length
                        ).toFixed(1)
                      : 0}
                    %
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 時系列グラフ */}
        <Card>
          <CardHeader>
            <CardTitle>混雑度の推移</CardTitle>
            <CardDescription>
              実測値と予測値の時系列データ（本日）
            </CardDescription>
          </CardHeader>
          <CardContent>
            {placeDetailLoading ? (
              <div className="flex justify-center items-center h-96">
                <div className="text-gray-500">読み込み中...</div>
              </div>
            ) : placeDetailError ? (
              <div className="flex justify-center items-center h-96">
                <div className="text-red-500">
                  エラー: {placeDetailError.message}
                </div>
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
                <ChartContainer config={chartConfig} className="h-96">
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="time"
                      tickLine={false}
                      axisLine={false}
                      className="text-xs"
                    />
                    <YAxis
                      tickLine={false}
                      axisLine={false}
                      className="text-xs"
                      domain={[0, 100]}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Line
                      type="monotone"
                      dataKey="actual"
                      stroke="var(--color-actual)"
                      strokeWidth={3}
                      dot={{
                        fill: "var(--color-actual)",
                        strokeWidth: 2,
                        r: 4,
                      }}
                      connectNulls={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted"
                      stroke="var(--color-predicted)"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={{
                        fill: "var(--color-predicted)",
                        strokeWidth: 2,
                        r: 3,
                      }}
                    />
                  </LineChart>
                </ChartContainer>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
