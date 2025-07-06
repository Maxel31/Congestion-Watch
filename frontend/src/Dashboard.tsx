import { usePlaceDetail, usePlaces } from "@/hooks/usePlaces";
import { usePolling } from "@/hooks/usePolling";
import { useEffect, useState } from "react";
import Header from "@/components/Header";
import PlaceSelector from "@/components/PlaceSelector";
import CurrentCongestionCard from "@/components/CurrentCongestionCard";
import StatisticsCard from "@/components/StatisticsCard";
import CongestionChart from "@/components/CongestionChart";

const Dashboard = () => {
  const [selectedPlaceId, setSelectedPlaceId] = useState<number | null>(null);
  const {
    places,
    loading: placesLoading,
    error: placesError,
    refetch: refreshPlaces,
  } = usePlaces();
  const {
    placeDetail,
    loading: placeDetailLoading,
    error: placeDetailError,
    refetch: refreshPlaceDetail,
  } = usePlaceDetail(selectedPlaceId || 0);

  usePolling(
    () => {
      refreshPlaces();
      if (selectedPlaceId) {
        refreshPlaceDetail();
      }
    },
    { interval: 60000 }
  );

  const selectedPlace = places.find((p) => p.id === selectedPlaceId);
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
          loading={placesLoading}
          error={placesError}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CurrentCongestionCard
            placeDetail={placeDetail}
            selectedPlaceName={selectedPlace?.name || "選択してください"}
            loading={placeDetailLoading}
            error={placeDetailError}
          />

          <StatisticsCard
            placeDetail={placeDetail}
            loading={placeDetailLoading}
            error={placeDetailError}
          />
        </div>

        <CongestionChart
          placeDetail={placeDetail}
          loading={placeDetailLoading}
          error={placeDetailError}
          currentTimestamp={currentTimestamp}
        />
      </div>
    </div>
  );
};

export default Dashboard;
