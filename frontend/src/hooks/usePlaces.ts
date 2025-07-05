import { mockPlaceDetails, mockPlaces } from '@/mocks/places';
import { apiService } from '@/services/api';
import { Place, PlaceDetail } from '@/types/api';
import { useEffect, useState } from 'react';

interface UsePlacesData {
  places: Place[];
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export const usePlaces = (): UsePlacesData => {
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchPlaces = async () => {
    setLoading(true);
    setError(null);

    try {
      try {
        const response = await apiService.getPlaces();
        setPlaces(response.places);
      } catch (err) {
        console.warn('Failed to fetch places from API, using mock data:', err);
        await new Promise(resolve => setTimeout(resolve, 500));
        setPlaces(mockPlaces);
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch places'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlaces();
  }, []);

  return {
    places: places,
    loading,
    error,
    refetch: fetchPlaces,
  };
};

interface UsePlaceDetailData {
  placeDetail: PlaceDetail | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export const usePlaceDetail = (placeId: number): UsePlaceDetailData => {
  const [placeDetail, setPlaceDetail] = useState<PlaceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchPlaceDetail = async () => {
    setLoading(true);
    setError(null);

    try {
      try {
        const response = await apiService.getPlaceDetail(placeId);
        setPlaceDetail(response.placeDetail);
      } catch (err) {
        console.warn(`Failed to fetch place detail for ID ${placeId}, using mock data:`, err);
        await new Promise(resolve => setTimeout(resolve, 500));
        const detail = mockPlaceDetails[placeId];
        if (!detail) {
          throw new Error('Place not found');
        }
        setPlaceDetail(detail);
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch place detail'));
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
    placeDetail: placeDetail,
    loading,
    error,
    refetch: fetchPlaceDetail,
  };
};