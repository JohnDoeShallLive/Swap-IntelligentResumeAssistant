import ChatWindow from '@/components/ChatWindow';

export default function ChatPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-transparent z-10 relative">
      <div className="w-full max-w-4xl px-4 flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold text-text-primary">Resume Assistant</h1>
        <a href="/" className="text-sm text-text-secondary hover:text-primary">Logout</a>
      </div>
      <ChatWindow />
    </main>
  );
}
