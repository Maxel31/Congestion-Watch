import { Clock } from "lucide-react";

interface HeaderProps {
  currentTimestamp: number;
}

const Header = ({ currentTimestamp }: HeaderProps) => {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Congestion Watch</h1>
      </div>
      <div className="flex items-center space-x-2 text-sm text-gray-600">
        <Clock className="w-4 h-4" />
        <span>
          {new Date(currentTimestamp).toLocaleTimeString("ja-JP", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
    </div>
  );
};

export default Header;