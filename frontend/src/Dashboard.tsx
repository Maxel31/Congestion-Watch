import ChartCard from "@/components/ChartCard";
import CurrentStatusCard from "@/components/CurrentStatusCard";
import Header from "@/components/Header";
import PlaceSelector from "@/components/PlaceSelector";
import StatisticsCard from "@/components/StatisticsCard";
import { Calendar } from "@/components/ui/calendar";
import { useTimeSeries } from "@/hooks/usePlaces";
import { usePolling } from "@/hooks/usePolling";
import { useEffect, useState } from "react";
import { places } from "./constants/places";

const Dashboard = () => {
  const [selectedPlaceId, setSelectedPlaceId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const { timeSeries, loading, error, refetch } = useTimeSeries(
    selectedPlaceId || 0
  );
  const [currentTimestamp, setCurrentTimestamp] = useState<number>(Date.now());

  usePolling(
    () => {
      if (selectedPlaceId) {
        refetch();
      }
    },
    { interval: 60000 }
  );

  const selectedPlace =
    places.find((place) => place.id === selectedPlaceId) || null;

  useEffect(() => {
    if (places.length > 0 && selectedPlaceId === null) {
      setSelectedPlaceId(places[0].id);
    }
  }, [selectedPlaceId]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTimestamp(Date.now());
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        <Header currentTimestamp={currentTimestamp} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PlaceSelector
            places={places}
            selectedPlaceId={selectedPlaceId}
            onSelectPlace={setSelectedPlaceId}
          />
          
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">日付選択</h2>
            <Calendar
              selected={selectedDate}
              onSelect={(date) => date && setSelectedDate(date)}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CurrentStatusCard
            timeSeries={timeSeries}
            place={selectedPlace}
            loading={loading}
            error={error}
          />

          <StatisticsCard
            timeSeries={timeSeries}
            place={selectedPlace}
            loading={loading}
            error={error}
          />
        </div>

        <ChartCard
          timeSeries={timeSeries}
          place={selectedPlace}
          loading={loading}
          error={error}
          currentTimestamp={currentTimestamp}
        />
      </div>
    </div>
  );
};

export default Dashboard;
