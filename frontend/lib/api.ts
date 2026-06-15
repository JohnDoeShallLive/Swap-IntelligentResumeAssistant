import { UploadResponse, AgentResponse } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function uploadResume(file?: File, text?: string): Promise<UploadResponse> {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  }
  if (text) {
    formData.append('text', text);
  }

  const res = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error('Failed to upload resume');
  }

  return res.json();
}

export async function chat(sessionId: string, query: string): Promise<AgentResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId, query }),
  });

  if (!res.ok) {
    throw new Error('Failed to fetch response from agent');
  }

  return res.json();
}
