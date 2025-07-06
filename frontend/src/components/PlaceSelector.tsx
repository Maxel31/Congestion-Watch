import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MapPin } from "lucide-react";
import { Place } from "@/types/api";

interface PlaceSelectorProps {
  places: Place[];
  selectedPlaceId: number | null;
  onSelectPlace: (placeId: number) => void;
  loading: boolean;
  error: Error | null;
}

const PlaceSelector = ({
  places,
  selectedPlaceId,
  onSelectPlace,
  loading,
  error,
}: PlaceSelectorProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <MapPin className="w-5 h-5 mr-2" />
          施設選択
        </CardTitle>
      </CardHeader>
      <CardContent className="flex justify-center h-16">
        {loading ? (
          <div className="flex justify-center items-center">
            <div className="text-gray-500">読み込み中...</div>
          </div>
        ) : error ? (
          <div className="flex justify-center items-center">
            <div className="text-red-500">エラー: {error.message}</div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 w-full">
            {places.map((place) => {
              return (
                <button
                  key={place.id}
                  onClick={() => onSelectPlace(place.id)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    selectedPlaceId === place.id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-gray-900">{place.name}</h3>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PlaceSelector;