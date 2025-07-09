import { places } from '@/constants/places';
import { TimeSeries } from '@/types/api';

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const baseUrl = 'https://backend.braveisland-6b119380.japanwest.azurecontainerapps.io';
    const url = `${baseUrl}/api${endpoint}`;

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

    const capacity = places.find(place => place.id === placeId)?.capacity || 0;

    return response.map(item => ({
      predictedScore: (item.predicted_score / capacity) * 100,
      actualScore: item.actual_score ? (item.actual_score / capacity) * 100 : undefined,
      targetDatetime: new Date(new Date(item.target_datetime).getTime() - 9 * 60 * 60 * 1000),
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