import { AlertCircle } from 'lucide-react';

export default function MissingDataAlert({ fields }: { fields: string[] }) {
  if (!fields || fields.length === 0) return null;

  return (
    <div className="mt-3 p-3 bg-red-50/50 border border-red-100 rounded-xl flex items-start gap-3">
      <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
      <div>
        <span className="text-xs font-semibold text-red-700 block mb-1">Missing Information:</span>
        <ul className="text-xs text-red-600 space-y-0.5">
          {fields.map((f, i) => (
            <li key={i} className="flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-red-400"></span>
              {f}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
