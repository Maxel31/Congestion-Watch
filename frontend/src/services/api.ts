import { FacilityDetailResponse, FacilityListResponse } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getFacilities(): Promise<FacilityListResponse> {
    return this.request<FacilityListResponse>('/facilities');
  }

  async getFacilityDetail(facilityId: number): Promise<FacilityDetailResponse> {
    return this.request<FacilityDetailResponse>(`/facilities/${facilityId}`);
  }

  async getPredictedScores(facilityId: number, hours: number = 24): Promise<any> {
    return this.request(`/facilities/${facilityId}/predictions?hours=${hours}`);
  }

  async getActualScores(facilityId: number, hours: number = 24): Promise<any> {
    return this.request(`/facilities/${facilityId}/actual?hours=${hours}`);
  }
}

export const apiService = new ApiService();