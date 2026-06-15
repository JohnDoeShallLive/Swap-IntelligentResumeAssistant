export default function ConfidenceBadge({ confidence, source }: { confidence: number, source: string }) {
  const percent = Math.round(confidence * 100);
  let colorClass = "bg-green-500";
  if (confidence < 0.7) colorClass = "bg-red-500";
  else if (confidence < 0.9) colorClass = "bg-yellow-500";

  return (
    <div className="flex items-center gap-4 mt-2 mb-2">
      <div className="flex items-center gap-2 w-48">
        <span className="text-xs font-semibold text-text-secondary w-20">Confidence</span>
        <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${percent}%` }}></div>
        </div>
        <span className="text-xs font-medium text-text-secondary">{percent}%</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-text-secondary">Source</span>
        <span className="text-xs text-text-primary bg-primary/10 px-2 py-0.5 rounded-full font-medium">
          {source}
        </span>
      </div>
    </div>
  );
}
