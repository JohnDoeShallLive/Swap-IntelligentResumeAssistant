'use client';
import { useState } from 'react';
import { uploadResume } from '@/lib/api';
import { UploadResponse } from '@/lib/types';
import { useRouter } from 'next/navigation';

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
    <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-gray-300 rounded-lg max-w-lg w-full bg-white shadow-sm">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Upload Candidate Resume</h2>
      <input 
        type="file" 
        accept="application/pdf" 
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="mb-4 block w-full text-sm text-gray-500
          file:mr-4 file:py-2 file:px-4
          file:rounded-full file:border-0
          file:text-sm file:font-semibold
          file:bg-blue-50 file:text-blue-700
          hover:file:bg-blue-100"
      />
      <div className="my-2 text-gray-500">OR paste text:</div>
      <textarea 
        value={text} 
        onChange={(e) => setText(e.target.value)} 
        placeholder="Paste resume text here..."
        className="w-full h-32 p-3 border rounded-md mb-4 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button 
        onClick={handleUpload} 
        disabled={loading || (!file && !text)}
        className="px-6 py-2 bg-blue-600 text-white rounded-full font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {loading ? 'Processing...' : 'Analyze Resume'}
      </button>
    </div>
  );
}
