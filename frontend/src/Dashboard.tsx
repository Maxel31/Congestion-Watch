import ChartCard from "@/components/ChartCard";
import CurrentStatusCard from "@/components/CurrentStatusCard";
import Header from "@/components/Header";
import PlaceSelector from "@/components/PlaceSelector";
import StatisticsCard from "@/components/StatisticsCard";
import { useTimeSeries } from "@/hooks/usePlaces";
import { usePolling } from "@/hooks/usePolling";
import { useEffect, useState } from "react";
import { places } from "./constants/places";

const Dashboard = () => {
  const [selectedPlaceId, setSelectedPlaceId] = useState<number | null>(null);
  const { timeSeries, loading, error, refetch } = useTimeSeries(
    selectedPlaceId || 0
  );

  usePolling(
    () => {
      if (selectedPlaceId) {
        refetch();
      }
    },
    { interval: 60000 }
  );

  const selectedPlace = places.find((p) => p.id === selectedPlaceId) || null;
  const [currentTimestamp, setCurrentTimestamp] = useState<number>(Date.now());

  useEffect(() => {
    if (places.length > 0 && selectedPlaceId === null) {
      setSelectedPlaceId(places[0].id);
    }
  }, [places, selectedPlaceId]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTimestamp(new Date().getTime());
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        <Header currentTimestamp={currentTimestamp} />

        <PlaceSelector
          places={places}
          selectedPlaceId={selectedPlaceId}
          onSelectPlace={setSelectedPlaceId}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CurrentStatusCard
            timeSeries={timeSeries}
            selectedPlace={selectedPlace}
            loading={loading}
            error={error}
          />

          <StatisticsCard
            timeSeries={timeSeries}
            loading={loading}
            error={error}
          />
        </div>

        <ChartCard
          timeSeries={timeSeries}
          loading={loading}
          error={error}
          currentTimestamp={currentTimestamp}
        />
      </div>
    </div>
  );
};

export default Dashboard;
