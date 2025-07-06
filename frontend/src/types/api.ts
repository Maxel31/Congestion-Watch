export interface Place {
  id: number;
  name: string;
  capacity: number;
  opens: { [day: number]: number[][] }
}

export interface TimeSeries {
  predictedScore?: number;
  actualScore?: number;
  targetDatetime: Date;
  placeId: number;
}
