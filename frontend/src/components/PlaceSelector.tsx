import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Place } from "@/types/api";
import { MapPin } from "lucide-react";

interface PlaceSelectorProps {
  places: Place[];
  selectedPlaceId: number | null;
  onSelectPlace: (placeId: number) => void;
}

const PlaceSelector = ({
  places,
  selectedPlaceId,
  onSelectPlace,
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
        <div className="grid grid-cols-2 gap-4 w-full">
          {places.map((place) => (
            <button
              key={place.id}
              onClick={() => onSelectPlace(place.id)}
              className={`p-4 rounded-lg border-2 transition-all ${
                selectedPlaceId === place.id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <h3 className="font-medium text-gray-900">{place.name}</h3>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default PlaceSelector;
