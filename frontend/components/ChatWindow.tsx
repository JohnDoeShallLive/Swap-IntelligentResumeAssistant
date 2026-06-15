'use client';
import { useState, useRef, useEffect } from 'react';
import { chat } from '@/lib/api';
import { ChatMessage, ResumeSummary } from '@/lib/types';
import MessageBubble from './MessageBubble';
import ResumeInsightsDrawer from './ResumeInsightsDrawer';
import { ArrowUp, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<ResumeSummary | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const s = sessionStorage.getItem('resume_summary');
    if (s) {
      setSummary(JSON.parse(s));
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (textOverride?: string) => {
    const textToSend = typeof textOverride === 'string' ? textOverride : input;
    if (!textToSend.trim()) return;
    const sessionId = sessionStorage.getItem('resume_session_id');
    if (!sessionId) {
      alert("No active session. Please go back and upload a resume.");
      return;
    }

    setMessages(prev => [...prev, { role: 'user', content: textToSend }]);
    if (typeof textOverride !== 'string') setInput('');
    setLoading(true);

    try {
      const res = await chat(sessionId, textToSend);
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: res.answer, 
        responseDetails: res 
      }]);
    } catch {
      setMessages(prev => [...prev, { role: 'agent', content: 'Sorry, there was an error processing your request.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] w-full max-w-4xl mx-auto rounded-xl overflow-hidden shadow-bubble bg-surface backdrop-blur-3xl border border-white/40 relative">
      {summary && (
        <div className="absolute top-4 right-4 z-20">
          <ResumeInsightsDrawer summary={summary} />
        </div>
      )}
      
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && summary && (
           <div className="flex flex-col items-center justify-center mt-20">
             <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-text-primary mb-2">Resume Processed!</h2>
              <p className="text-text-secondary">What would you like to know about {summary.name || 'the candidate'}?</p>
            </div>
           </div>
        )}
        
        {messages.map((m, i) => (
          <MessageBubble key={i} msg={m} />
        ))}
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-white shadow-bubble rounded-3xl px-6 py-4 flex items-center gap-2">
               <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="flex items-center gap-2 text-primary text-sm font-medium"
               >
                 <Sparkles size={16} />
                 Analyzing candidate...
               </motion.div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 flex flex-col gap-3 z-10 bg-white/10 backdrop-blur-md border-t border-white/20">
        <div className="flex gap-2 px-2 overflow-x-auto pb-1 hide-scrollbar">
           <button onClick={() => handleSend("Give me a resume summary")} className="whitespace-nowrap px-4 py-2 bg-white/70 hover:bg-white text-text-primary text-sm font-medium rounded-full shadow-sm border border-white transition-colors">Resume Summary</button>
           <button onClick={() => handleSend("What is the candidate's skill match for a frontend role?")} className="whitespace-nowrap px-4 py-2 bg-white/70 hover:bg-white text-text-primary text-sm font-medium rounded-full shadow-sm border border-white transition-colors">Skill Match</button>
           <button onClick={() => handleSend("Calculate a candidate score")} className="whitespace-nowrap px-4 py-2 bg-white/70 hover:bg-white text-text-primary text-sm font-medium rounded-full shadow-sm border border-white transition-colors">Candidate Score</button>
           <button onClick={() => handleSend("What skills are missing?")} className="whitespace-nowrap px-4 py-2 bg-white/70 hover:bg-white text-text-primary text-sm font-medium rounded-full shadow-sm border border-white transition-colors">Missing Skills</button>
        </div>

        <div className="h-[80px] bg-white/35 backdrop-blur-[20px] rounded-[24px] p-2 flex items-center gap-3 border border-white/50 shadow-sm relative">
          <input
            type="text"
            className="flex-1 h-full px-6 bg-transparent focus:outline-none text-text-primary placeholder:text-gray-500 font-medium"
            placeholder="Evaluate candidate for a DevOps role..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={loading}
          />
          <button 
            className="w-[52px] h-[52px] rounded-full bg-gradient-to-b from-[#4F5DFF] to-[#6678FF] flex items-center justify-center text-white shadow-md hover:opacity-90 disabled:opacity-50 transition-all flex-shrink-0"
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
          >
            <ArrowUp size={24} />
          </button>
        </div>
      </div>
    </div>
  );
}
