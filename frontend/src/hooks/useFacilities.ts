import { useState, useEffect } from 'react';
import { Facility, FacilityDetail } from '@/types/api';
import { mockFacilities, mockFacilityDetails } from '@/mocks/facilityData';
import { apiService } from '@/services/api';

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
      // 実際のAPI呼び出しを試行、失敗時はモックデータを使用
      try {
        const response = await apiService.getFacilities();
        setFacilities(response.facilities);
      } catch (apiError) {
        console.warn('API呼び出しに失敗しました。モックデータを使用します:', apiError);
        // モックデータの使用（API呼び出しをシミュレート）
        await new Promise(resolve => setTimeout(resolve, 500));
        setFacilities(mockFacilities);
      }
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
      // 実際のAPI呼び出しを試行、失敗時はモックデータを使用
      try {
        const response = await apiService.getFacilityDetail(facilityId);
        setFacilityDetail(response.facilityDetail);
      } catch (apiError) {
        console.warn('API呼び出しに失敗しました。モックデータを使用します:', apiError);
        // モックデータの使用（API呼び出しをシミュレート）
        await new Promise(resolve => setTimeout(resolve, 500));
        const detail = mockFacilityDetails[facilityId];
        if (!detail) {
          throw new Error('Facility not found');
        }
        setFacilityDetail(detail);
      }
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