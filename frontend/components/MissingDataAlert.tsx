export default function MissingDataAlert({ fields }: { fields: string[] }) {
  if (!fields || fields.length === 0) return null;

  return (
    <div className="mt-2 p-2 bg-orange-50 border border-orange-200 rounded-md">
      <span className="text-xs font-semibold text-orange-700">Missing Data Detected:</span>
      <ul className="list-disc list-inside text-xs text-orange-600 mt-1">
        {fields.map((f, i) => <li key={i}>{f}</li>)}
      </ul>
    </div>
  );
}
