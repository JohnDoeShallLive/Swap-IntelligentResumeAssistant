import ResumeUpload from '@/components/ResumeUpload';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-transparent z-10 relative">
      <div className="w-full max-w-4xl px-4 flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold text-text-primary">Resume Assistant</h1>
        <div className="text-sm text-text-secondary cursor-pointer hover:text-primary">Profile / Logout</div>
      </div>
      <div className="flex flex-col h-[calc(100vh-100px)] w-full max-w-4xl mx-auto rounded-xl overflow-hidden shadow-bubble bg-surface backdrop-blur-3xl border border-white/40">
        <div className="flex-1 overflow-y-auto p-6 space-y-4 flex flex-col justify-center items-center">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-text-primary mb-2">👋 Hey! How may I assist you today?</h2>
              <p className="text-text-secondary">Upload a resume or ask questions about an analyzed candidate.</p>
            </div>
            <ResumeUpload />
        </div>
      </div>
    </main>
  );
}
