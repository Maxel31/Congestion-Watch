import { useState, useEffect } from 'react';
import { Facility, FacilityDetail } from '@/types/api';
import { mockFacilities, mockFacilityDetails } from '@/mocks/facilityData';

interface UseFacilitiesReturn {
  facilities: Facility[];
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export const useFacilities = (): UseFacilitiesReturn => {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchFacilities = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // TODO: 実際のAPI実装時にはここを置き換える
      // const response = await fetch('/api/facilities');
      // const data = await response.json();
      // setFacilities(data.facilities);
      
      // モックデータの使用（API呼び出しをシミュレート）
      await new Promise(resolve => setTimeout(resolve, 500));
      setFacilities(mockFacilities);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch facilities'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFacilities();
  }, []);

  return {
    facilities,
    loading,
    error,
    refetch: fetchFacilities,
  };
};

interface UseFacilityDetailReturn {
  facilityDetail: FacilityDetail | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export const useFacilityDetail = (facilityId: number): UseFacilityDetailReturn => {
  const [facilityDetail, setFacilityDetail] = useState<FacilityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchFacilityDetail = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // TODO: 実際のAPI実装時にはここを置き換える
      // const response = await fetch(`/api/facilities/${facilityId}`);
      // const data = await response.json();
      // setFacilityDetail(data.facilityDetail);
      
      // モックデータの使用（API呼び出しをシミュレート）
      await new Promise(resolve => setTimeout(resolve, 500));
      const detail = mockFacilityDetails[facilityId];
      if (!detail) {
        throw new Error('Facility not found');
      }
      setFacilityDetail(detail);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch facility detail'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (facilityId) {
      fetchFacilityDetail();
    }
  }, [facilityId]);

  return {
    facilityDetail,
    loading,
    error,
    refetch: fetchFacilityDetail,
  };
};