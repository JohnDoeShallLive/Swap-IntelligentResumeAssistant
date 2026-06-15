'use client';
import { useState } from 'react';
import { uploadResume } from '@/lib/api';
import { UploadResponse } from '@/lib/types';
import { useRouter } from 'next/navigation';
import { FileUp } from 'lucide-react';

export default function ResumeUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleUpload = async () => {
    setLoading(true);
    try {
      const res: UploadResponse = await uploadResume(file || undefined, text || undefined);
      // Store session ID to use in chat
      sessionStorage.setItem('resume_session_id', res.session_id);
      sessionStorage.setItem('resume_summary', JSON.stringify(res.resume_summary));
      router.push('/chat');
    } catch (e) {
      alert('Error uploading resume: ' + e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 border border-white/50 rounded-2xl max-w-md w-full bg-surface backdrop-blur-[20px] shadow-bubble">
      <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4 text-primary">
        <FileUp size={24} />
      </div>
      <h2 className="text-lg font-semibold mb-2 text-text-primary">Upload Resume</h2>
      <p className="text-sm text-text-secondary mb-6">PDF / DOCX / TXT</p>
      
      <input 
        type="file" 
        accept="application/pdf,.docx,.txt" 
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="mb-4 block w-full text-sm text-text-secondary
          file:mr-4 file:py-2 file:px-4
          file:rounded-full file:border-0
          file:text-sm file:font-semibold
          file:bg-primary/10 file:text-primary
          hover:file:bg-primary/20"
      />
      <div className="my-2 text-text-secondary text-xs font-medium uppercase tracking-wider">OR paste text:</div>
      <textarea 
        value={text} 
        onChange={(e) => setText(e.target.value)} 
        placeholder="Paste resume text here..."
        className="w-full h-24 p-3 border border-white/50 bg-white/50 rounded-xl mb-4 text-text-primary focus:outline-none focus:ring-2 focus:ring-primary backdrop-blur-sm placeholder:text-gray-400"
      />
      <button 
        onClick={handleUpload} 
        disabled={loading || (!file && !text)}
        className="w-full py-3 bg-gradient-to-r from-primary to-[#6678FF] text-white rounded-full font-medium hover:opacity-90 disabled:opacity-50 transition-all shadow-md"
      >
        {loading ? 'Processing...' : 'Analyze Candidate'}
      </button>
    </div>
  );
}
