import { places } from '@/constants/places';
import { TimeSeries } from '@/types/api';

const BASE_URL = 'https://backend.braveisland-6b119380.japanwest.azurecontainerapps.io';

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${BASE_URL}/api${endpoint}`;

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
    const today = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Tokyo'
    }).format(new Date());

    const response = await this.request<CloudDataResponse[]>(`/cloud-data/${placeId}/${today}`);
    const place = places.find(place => place.id === placeId);
    const capacity = place?.capacity || 0;

    return response
      .map(item => ({
        predictedScore: (item.predicted_score / capacity) * 100,
        actualScore: item.actual_score ? (item.actual_score / capacity) * 100 : undefined,
        targetDatetime: new Date(new Date(item.target_datetime).getTime() - 9 * 60 * 60 * 1000),
        placeId: item.place_id
      }))
      .sort((a, b) => a.targetDatetime.getTime() - b.targetDatetime.getTime());
  }
}

interface CloudDataResponse {
  predicted_score: number;
  actual_score?: number;
  target_datetime: string;
  place_id: number;
}

export const apiService = new ApiService();
