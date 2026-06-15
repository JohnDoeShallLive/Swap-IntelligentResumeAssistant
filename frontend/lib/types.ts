export interface ResumeSummary {
  name: string | null;
  skills: string[];
  experience_count: number;
  education_count: number;
}

export interface UploadResponse {
  session_id: string;
  resume_summary: ResumeSummary;
}

export interface AgentResponse {
  answer: string;
  confidence: number;
  source: 'resume' | 'inference';
  missing_data: string[];
}

export interface ChatMessage {
  role: 'user' | 'agent';
  content: string;
  responseDetails?: AgentResponse;
}
