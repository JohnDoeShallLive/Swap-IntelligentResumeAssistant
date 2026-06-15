import { ChatMessage } from '@/lib/types';
import ConfidenceBadge from './ConfidenceBadge';
import MissingDataAlert from './MissingDataAlert';
import { motion } from 'framer-motion';

export default function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isAgent = msg.role === 'agent';

  return (
    <div className={`flex w-full ${isAgent ? 'justify-start' : 'justify-end'} mb-6`}>
      <motion.div 
        initial={{ opacity: 0, scale: 0.98, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`max-w-[80%] rounded-3xl px-6 py-4 shadow-bubble ${isAgent ? 'bg-white text-text-primary' : 'bg-gradient-to-br from-[#6678FF] to-primary text-white'}`}
      >
        <div className="text-[15px] leading-relaxed">{msg.content}</div>
        {isAgent && msg.responseDetails && (
          <div className="mt-4 pt-4 border-t border-gray-100/50">
            <ConfidenceBadge 
              confidence={msg.responseDetails.confidence} 
              source={msg.responseDetails.source} 
            />
            <MissingDataAlert fields={msg.responseDetails.missing_data} />
          </div>
        )}
      </motion.div>
    </div>
  );
}
