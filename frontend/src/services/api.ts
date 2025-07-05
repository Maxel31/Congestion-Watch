import { PlaceDetailResponse, PlaceListResponse } from '@/types/api';

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
      throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
    }

    return response.json();
  }

  async getPlaces(): Promise<PlaceListResponse> {
    return this.request<PlaceListResponse>('/places');
  }

  async getPlaceDetail(placeId: number): Promise<PlaceDetailResponse> {
    return this.request<PlaceDetailResponse>(`/place/${placeId}`);
  }
}

export const apiService = new ApiService();