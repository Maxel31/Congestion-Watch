import { Place } from "@/types/api";

const HOUR_MS = 60 * 60 * 1000;
const NORTH_CAFETERIA_HOURS = [[11 * HOUR_MS, 14 * HOUR_MS]];
const SOUTH_CAFETERIA_HOURS = [
  [11 * HOUR_MS, 14.5 * HOUR_MS],
  [17 * HOUR_MS, 19 * HOUR_MS]
];

export const places: Place[] = [
  {
    id: 2,
    name: '北館食堂',
    capacity: 70,
    opens: {
      0: [],
      1: NORTH_CAFETERIA_HOURS,
      2: NORTH_CAFETERIA_HOURS,
      3: NORTH_CAFETERIA_HOURS,
      4: NORTH_CAFETERIA_HOURS,
      5: NORTH_CAFETERIA_HOURS,
      6: [],
    },
    range: [10, 15]
  },
  {
    id: 1,
    name: '南館食堂',
    capacity: 250,
    opens: {
      0: [],
      1: SOUTH_CAFETERIA_HOURS,
      2: SOUTH_CAFETERIA_HOURS,
      3: SOUTH_CAFETERIA_HOURS,
      4: SOUTH_CAFETERIA_HOURS,
      5: SOUTH_CAFETERIA_HOURS,
      6: [],
    },
    range: [10, 20],
  },
];
