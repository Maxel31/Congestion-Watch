interface SpeedMeterProps {
  value?: number;
}

const CROWDNESS_LEVELS = [
  { threshold: 30, color: "#22c55e", label: "空いている" },
  { threshold: 60, color: "#f59e0b", label: "普通" },
  { threshold: 80, color: "#f97316", label: "やや混雑" },
  { threshold: 100, color: "#ef4444", label: "混雑" },
  { threshold: Infinity, color: "#dc2626", label: "非常に混雑" },
];

const getCrowdnessInfo = (value: number) => {
  const level = CROWDNESS_LEVELS.find((level) => value <= level.threshold);
  return { color: level!.color, label: level!.label };
};

const SpeedMeter = ({ value }: SpeedMeterProps) => {
  const { color, label } =
    value !== undefined
      ? getCrowdnessInfo(value)
      : { color: "#9ca3af", label: "不明" };

  return (
    <div className="relative w-full h-full">
      <svg
        viewBox="0 0 220 130"
        className="w-full h-full"
        preserveAspectRatio="xMidYMid meet"
      >
        <path
          d="M 10 110 A 100 100 0 0 1 210 110"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="8"
          strokeLinecap="round"
        />
        <path
          d="M 10 110 A 100 100 0 0 1 210 110"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={Math.PI * 105}
          strokeDashoffset={
            value !== undefined
              ? Math.PI * 105 - (Math.min(value, 100) / 100) * Math.PI * 105
              : Math.PI * 105
          }
          className="transition-all duration-1000 ease-out"
        />
        {[0, 25, 50, 75, 100].map((tick) => {
          const angle = (tick / 100) * Math.PI;
          const centerX = 110;
          const centerY = 110;
          const outerRadius = 90;
          const innerRadius = 80;

          const x1 = centerX + outerRadius * Math.cos(angle);
          const y1 = centerY - outerRadius * Math.sin(angle);
          const x2 = centerX + innerRadius * Math.cos(angle);
          const y2 = centerY - innerRadius * Math.sin(angle);

          return (
            <line
              key={tick}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#9ca3af"
              strokeWidth="2"
            />
          );
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center mt-8">
        <div className="text-sm text-gray-600">{label}</div>
        <div className="text-4xl font-bold text-gray-800">
          {value !== undefined ? `${value}%` : "不明"}
        </div>
      </div>
    </div>
  );
};

export default SpeedMeter;
