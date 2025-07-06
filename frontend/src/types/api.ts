export interface Place {
  id: number;
  name: string;
  capacity: number;
  opens: { [day: number]: number[][] }
}

export interface TimeSeries {
  timestamp: Date;
  actualScore?: number;
  predictedScore?: number;
}
