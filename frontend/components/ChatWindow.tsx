'use client';
import { useState, useRef, useEffect } from 'react';
import { chat } from '@/lib/api';
import { ChatMessage, ResumeSummary } from '@/lib/types';
import MessageBubble from './MessageBubble';

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
      setMessages([{ role: 'agent', content: 'Resume loaded successfully! What would you like to know about the candidate?' }]);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const sessionId = sessionStorage.getItem('resume_session_id');
    if (!sessionId) {
      alert("No active session. Please go back and upload a resume.");
      return;
    }

    const userMsg = input;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await chat(sessionId, userMsg);
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: res.answer, 
        responseDetails: res 
      }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'agent', content: 'Sorry, there was an error processing your request.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] w-full max-w-4xl mx-auto bg-gray-50 rounded-xl overflow-hidden border shadow-sm">
      {summary && (
        <div className="bg-white border-b px-6 py-4 flex justify-between items-center shadow-sm z-10">
          <div>
            <h2 className="font-semibold text-gray-800">{summary.name || 'Unknown Candidate'}</h2>
            <p className="text-xs text-gray-500">{summary.skills.slice(0, 5).join(', ')}</p>
          </div>
          <div className="text-xs text-gray-400">Active Session</div>
        </div>
      )}
      
      <div className="flex-1 overflow-y-auto p-6 space-y-2">
        {messages.map((m, i) => (
          <MessageBubble key={i} msg={m} />
        ))}
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-white border rounded-2xl px-5 py-3 text-sm text-gray-400 italic">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="bg-white p-4 border-t">
        <div className="flex items-center gap-3">
          <input
            type="text"
            className="flex-1 p-3 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50 text-gray-900"
            placeholder="e.g., Does this candidate know Docker?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={loading}
          />
          <button 
            className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors disabled:opacity-50"
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
