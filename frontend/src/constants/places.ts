import { Place } from "@/types/api";

const HOUR_MS = 60 * 60 * 1000;
const NORTH_OPEN = [[11 * HOUR_MS, 14 * HOUR_MS]];
const SOUTH_OPEN = [[11 * HOUR_MS, 14.5 * HOUR_MS], [17 * HOUR_MS, 19 * HOUR_MS]];

export const places: Place[] = [
    {
        id: 1,
        name: '北館食堂',
        capacity: 100,
        opens: {
            0: [],
            1: NORTH_OPEN,
            2: NORTH_OPEN,
            3: NORTH_OPEN,
            4: NORTH_OPEN,
            5: NORTH_OPEN,
            6: [],
        }
    },
    {
        id: 2,
        name: '南館食堂',
        capacity: 400,
        opens: {
            0: [],
            1: SOUTH_OPEN,
            2: SOUTH_OPEN,
            3: SOUTH_OPEN,
            4: SOUTH_OPEN,
            5: SOUTH_OPEN,
            6: [],
        }
    },
];
