import { ChatMessage } from '@/lib/types';
import ConfidenceBadge from './ConfidenceBadge';
import MissingDataAlert from './MissingDataAlert';

export default function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isAgent = msg.role === 'agent';

  return (
    <div className={`flex w-full ${isAgent ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${isAgent ? 'bg-white border text-gray-800 shadow-sm' : 'bg-blue-600 text-white shadow-md'}`}>
        <div className="text-sm">{msg.content}</div>
        {isAgent && msg.responseDetails && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <ConfidenceBadge 
              confidence={msg.responseDetails.confidence} 
              source={msg.responseDetails.source} 
            />
            <MissingDataAlert fields={msg.responseDetails.missing_data} />
          </div>
        )}
      </div>
    </div>
  );
}
