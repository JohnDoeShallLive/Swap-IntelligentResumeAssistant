import ChatWindow from '@/components/ChatWindow';

export default function ChatPage() {
  return (
    <main className="flex min-h-screen flex-col items-center pt-8 bg-gray-100">
      <div className="w-full max-w-4xl px-4 flex justify-between items-end mb-4">
        <h1 className="text-2xl font-bold text-gray-800">Resume Evaluation</h1>
        <a href="/" className="text-sm text-blue-600 hover:underline">← Upload another resume</a>
      </div>
      <ChatWindow />
    </main>
  );
}
