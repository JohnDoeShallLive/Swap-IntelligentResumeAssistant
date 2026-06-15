export default function ConfidenceBadge({ confidence, source }: { confidence: number, source: string }) {
  let color = "bg-green-100 text-green-800";
  if (confidence < 0.7) color = "bg-red-100 text-red-800";
  else if (confidence < 0.9) color = "bg-yellow-100 text-yellow-800";

  return (
    <div className="flex items-center gap-2 mt-2">
      <span className={`text-xs font-medium px-2 py-1 rounded ${color}`}>
        Confidence: {Math.round(confidence * 100)}%
      </span>
      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
        Source: {source}
      </span>
    </div>
  );
}
