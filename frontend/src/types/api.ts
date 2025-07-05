export interface Place {
  id: number;
  name: string;
}

export interface TimeSeries {
  timestamp: string;
  actualScore?: number;
  predictedScore?: number;
}

export interface PlaceDetail {
  place: Place;
  timeSeries: TimeSeries[];
}

export interface PlaceListResponse {
  places: Place[];
}

export interface PlaceDetailResponse {
  placeDetail: PlaceDetail;
}