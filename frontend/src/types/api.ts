export interface Facility {
  id: number;
  name: string;
  currentScore: number;
  capacity: number;
  occupancyRate: number;
}

export interface TimeSeriesData {
  timestamp: string;
  actualScore: number;
  predictedScore?: number;
}

export interface FacilityDetail {
  facility: Facility;
  timeSeries: TimeSeriesData[];
}

export interface FacilityListResponse {
  facilities: Facility[];
  lastUpdated: string;
}

export interface FacilityDetailResponse {
  facilityDetail: FacilityDetail;
}