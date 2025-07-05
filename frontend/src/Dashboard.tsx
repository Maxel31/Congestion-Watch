import { Badge } from "@/components/ui/badge";
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
import { Clock, MapPin, TrendingUp, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";

const Dashboard = () => {
  const [currentCrowdness, setCurrentCrowdness] = useState(65);
  const [selectedFacility, setSelectedFacility] = useState("メインホール");

  // サンプルデータ
  const timeSeriesData = [
    { time: "9:00", actual: 20, predicted: 25, hour: 9 },
    { time: "10:00", actual: 35, predicted: 40, hour: 10 },
    { time: "11:00", actual: 45, predicted: 50, hour: 11 },
    { time: "12:00", actual: 75, predicted: 70, hour: 12 },
    { time: "13:00", actual: 85, predicted: 80, hour: 13 },
    { time: "14:00", actual: 65, predicted: 75, hour: 14 },
    { time: "15:00", actual: null, predicted: 60, hour: 15 },
    { time: "16:00", actual: null, predicted: 70, hour: 16 },
    { time: "17:00", actual: null, predicted: 80, hour: 17 },
    { time: "18:00", actual: null, predicted: 90, hour: 18 },
    { time: "19:00", actual: null, predicted: 75, hour: 19 },
    { time: "20:00", actual: null, predicted: 45, hour: 20 },
  ];

  const facilities = [
    { name: "メインホール", crowdness: 65, capacity: 200 },
    { name: "会議室A", crowdness: 30, capacity: 50 },
    { name: "会議室B", crowdness: 80, capacity: 30 },
    { name: "カフェテリア", crowdness: 45, capacity: 100 },
  ];

  // 混雑度に基づく色とラベル
  const getCrowdnessInfo = (value) => {
    if (value <= 30)
      return { color: "#22c55e", label: "空いている", bgColor: "bg-green-100" };
    if (value <= 60)
      return { color: "#f59e0b", label: "普通", bgColor: "bg-yellow-100" };
    if (value <= 80)
      return { color: "#f97316", label: "混雑", bgColor: "bg-orange-100" };
    return { color: "#ef4444", label: "非常に混雑", bgColor: "bg-red-100" };
  };

  // スピードメータコンポーネント
  const SpeedMeter = ({ value, size = 200 }) => {
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
    // 選択された施設の混雑度を更新
    const facility = facilities.find((f) => f.name === selectedFacility);
    if (facility) {
      setCurrentCrowdness(facility.crowdness);
    }
  }, [selectedFacility]);

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
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {facilities.map((facility) => {
                const { color, label, bgColor } = getCrowdnessInfo(
                  facility.crowdness
                );
                return (
                  <button
                    key={facility.name}
                    onClick={() => setSelectedFacility(facility.name)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      selectedFacility === facility.name
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-gray-900">
                        {facility.name}
                      </h3>
                      <Badge variant="secondary" className={bgColor}>
                        {facility.crowdness}%
                      </Badge>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Users className="w-4 h-4 mr-1" />
                      <span>定員: {facility.capacity}名</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{label}</div>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* メインダッシュボード */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 現在の混雑度 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Users className="w-5 h-5 mr-2" />
                現在の混雑度 - {selectedFacility}
              </CardTitle>
              <CardDescription>リアルタイムの混雑状況</CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
              <SpeedMeter value={currentCrowdness} size={250} />
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
                    {currentCrowdness}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">
                    今日の最高混雑度
                  </span>
                  <span className="text-lg font-semibold text-red-600">
                    85%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">平均混雑度</span>
                  <span className="text-lg font-semibold text-blue-600">
                    58%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">
                    次の混雑ピーク予測
                  </span>
                  <span className="text-lg font-semibold text-orange-600">
                    18:00 (90%)
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
                  dot={{ fill: "var(--color-actual)", strokeWidth: 2, r: 4 }}
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="var(--color-predicted)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={{ fill: "var(--color-predicted)", strokeWidth: 2, r: 3 }}
                />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
