import { TimeSeries } from '@/types/api';

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `/api${endpoint}`;

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
    }

    return response.json();
  }



  async getPlace(placeId: number): Promise<TimeSeries[]> {
    const today = new Date().toISOString().split('T')[0];
    const response = await this.request<CloudDataResponse[]>(`/cloud-data/${placeId}/${today}`);

    return response.map(item => ({
      predictedScore: item.predicted_score,
      actualScore: item.actual_score,
      targetDatetime: new Date(item.target_datetime),
      placeId: item.place_id
    }));
  }
}

interface CloudDataResponse {
  predicted_score: number;
  actual_score?: number;
  target_datetime: string;
  place_id: number;
}

export const apiService = new ApiService();