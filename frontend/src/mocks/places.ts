import { Place, PlaceDetail, TimeSeries } from '@/types/api';

export const mockPlaces: Place[] = [
  {
    id: 1,
    name: '北館食堂',
  },
  {
    id: 2,
    name: '南館食堂',
  },
];

const generateTimeSeriesData = (): TimeSeries[] => {
  const now = new Date();
  const data: TimeSeries[] = [];

  // その日の0時から23時55分までのデータを5分間隔で生成
  const startOfDay = new Date(now);
  startOfDay.setHours(0, 0, 0, 0);

  for (let i = 0; i < 288; i++) {
    const timestamp = new Date(startOfDay.getTime() + i * 5 * 60 * 1000);
    const hour = timestamp.getHours();

    // 施設ごとの混雑パターン
    let baseScore = 30;
    if (hour >= 11 && hour <= 13) baseScore = 80;
    else if (hour >= 17 && hour <= 19) baseScore = 70;
    else if (hour >= 7 && hour <= 9) baseScore = 50;

    // ランダムな変動を追加
    const variation = Math.floor(Math.random() * 20) - 10;
    const actualScore = Math.max(0, Math.min(100, baseScore + variation));

    // 未来のデータには予測値も含める
    const predictedScore = actualScore + Math.floor(Math.random() * 10) - 5;

    // 現在時刻以降はactualScoreを含めない
    const isFuture = timestamp > now;

    data.push({
      timestamp: timestamp.toISOString(),
      actualScore: isFuture ? undefined : actualScore,
      predictedScore,
    });
  }
  return data;
};

export const mockPlaceDetails: Record<number, PlaceDetail> = {
  1: {
    place: mockPlaces[0],
    timeSeries: generateTimeSeriesData(),
  },
  2: {
    place: mockPlaces[1],
    timeSeries: generateTimeSeriesData(),
  },
};