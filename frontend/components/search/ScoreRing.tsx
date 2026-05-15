"use client";

interface Props {
  score: number; // 0-100
  size?: number;
}

export function ScoreRing({ score, size = 60 }: Props) {
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;

  const color =
    score >= 85 ? "#22c55e"   // green-500
    : score >= 65 ? "#f59e0b" // amber-500
    : "#ef4444";              // red-500

  const trackColor =
    score >= 85 ? "#dcfce7"
    : score >= 65 ? "#fef3c7"
    : "#fee2e2";

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={trackColor} strokeWidth={7} />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none"
          stroke={color}
          strokeWidth={7}
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center text-xs font-bold"
        style={{ color }}
      >
        {score}
      </span>
    </div>
  );
}
