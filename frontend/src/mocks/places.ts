import { TimeSeries } from '@/types/api';

const TIME_INTERVAL_MINUTES = 5;
const INTERVALS_PER_DAY = 288;
const VARIATION_RANGE = 20;
const PREDICTION_VARIANCE = 10;

const getBaseCongestionScore = (hour: number): number => {
  if (hour >= 11 && hour <= 13) return 80;
  if (hour >= 17 && hour <= 19) return 70;
  if (hour >= 7 && hour <= 9) return 50;
  return 30;
};

const generateTimeSeriesData = (placeId: number): TimeSeries[] => {
  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  return Array.from({ length: INTERVALS_PER_DAY }, (_, i) => {
    const timestamp = new Date(startOfDay.getTime() + i * TIME_INTERVAL_MINUTES * 60 * 1000);
    const hour = timestamp.getHours();

    const baseScore = getBaseCongestionScore(hour);
    const variation = Math.floor(Math.random() * VARIATION_RANGE) - VARIATION_RANGE / 2;
    const actualScore = Math.max(0, Math.min(100, baseScore + variation));
    const predictedScore = actualScore + Math.floor(Math.random() * PREDICTION_VARIANCE) - PREDICTION_VARIANCE / 2;
    const isFuture = timestamp > now;

    return {
      placeId,
      targetDatetime: timestamp,
      actualScore: isFuture ? undefined : actualScore,
      predictedScore,
    };
  });
};

export const mockPlaceDetails: Record<number, TimeSeries[]> = {
  1: generateTimeSeriesData(1),
  2: generateTimeSeriesData(2),
};