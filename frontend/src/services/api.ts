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
    return this.request<TimeSeries[]>(`/places/${placeId}`);
  }
}

export const apiService = new ApiService();