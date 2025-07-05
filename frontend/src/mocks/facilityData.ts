import { Facility, TimeSeriesData, FacilityDetail } from '@/types/api';

export const mockFacilities: Facility[] = [
  {
    id: 1,
    name: '北館食堂',
    currentScore: 65,
    capacity: 200,
    occupancyRate: 0.65,
  },
  {
    id: 2,
    name: '南館食堂',
    currentScore: 45,
    capacity: 150,
    occupancyRate: 0.45,
  },
  {
    id: 3,
    name: '図書館',
    currentScore: 80,
    capacity: 300,
    occupancyRate: 0.80,
  },
  {
    id: 4,
    name: '体育館',
    currentScore: 30,
    capacity: 100,
    occupancyRate: 0.30,
  },
];

const generateTimeSeriesData = (facilityId: number): TimeSeriesData[] => {
  const now = new Date();
  const data: TimeSeriesData[] = [];
  
  // 過去24時間のデータを30分間隔で生成
  for (let i = 48; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 30 * 60 * 1000);
    const hour = timestamp.getHours();
    
    // 施設ごとの混雑パターン
    let baseScore = 30;
    if (facilityId === 1 || facilityId === 2) {
      // 食堂: 昼食・夕食時に混雑
      if (hour >= 11 && hour <= 13) baseScore = 80;
      else if (hour >= 17 && hour <= 19) baseScore = 70;
      else if (hour >= 7 && hour <= 9) baseScore = 50;
    } else if (facilityId === 3) {
      // 図書館: 午後から夜にかけて混雑
      if (hour >= 14 && hour <= 21) baseScore = 70;
      else if (hour >= 10 && hour <= 14) baseScore = 50;
    } else if (facilityId === 4) {
      // 体育館: 夕方に混雑
      if (hour >= 16 && hour <= 20) baseScore = 60;
    }
    
    // ランダムな変動を追加
    const variation = Math.floor(Math.random() * 20) - 10;
    const actualScore = Math.max(0, Math.min(100, baseScore + variation));
    
    // 未来のデータには予測値も含める
    const isFuture = i === 0;
    const predictedScore = isFuture ? actualScore + Math.floor(Math.random() * 10) - 5 : undefined;
    
    data.push({
      timestamp: timestamp.toISOString(),
      actualScore: isFuture ? 0 : actualScore,
      predictedScore,
    });
  }
  
  return data;
};

export const mockFacilityDetails: Record<number, FacilityDetail> = {
  1: {
    facility: mockFacilities[0],
    timeSeries: generateTimeSeriesData(1),
  },
  2: {
    facility: mockFacilities[1],
    timeSeries: generateTimeSeriesData(2),
  },
  3: {
    facility: mockFacilities[2],
    timeSeries: generateTimeSeriesData(3),
  },
  4: {
    facility: mockFacilities[3],
    timeSeries: generateTimeSeriesData(4),
  },
};