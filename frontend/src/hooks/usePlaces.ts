import { mockPlaceDetails as mockTimeSeries } from '@/mocks/places';
import { apiService } from '@/services/api';
import { TimeSeries } from '@/types/api';
import { useEffect, useState } from 'react';

interface UsePlaceDetailData {
  timeSeries: TimeSeries[] | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export const useTimeSeries = (placeId: number): UsePlaceDetailData => {
  const [timeSeries, setTimeSeries] = useState<TimeSeries[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchPlaceDetail = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.getPlace(placeId);
      setTimeSeries(response);
    } catch (err) {
      console.warn(`Failed to fetch place detail for ID ${placeId}, using mock data:`, err);
      
      try {
        await new Promise(resolve => setTimeout(resolve, 500));
        const detail = mockTimeSeries[placeId];
        if (!detail) throw new Error('Place not found');
        setTimeSeries(detail);
      } catch (mockErr) {
        setError(mockErr instanceof Error ? mockErr : new Error('Failed to fetch place detail'));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (placeId) {
      fetchPlaceDetail();
    }
  }, [placeId]);

  return {
    timeSeries,
    loading,
    error,
    refetch: fetchPlaceDetail,
  };
};