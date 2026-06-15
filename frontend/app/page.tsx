import ResumeUpload from '@/components/ResumeUpload';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-gray-50">
      <div className="mb-10 text-center">
        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight mb-3">
          Intelligent <span className="text-blue-600">Resume</span> Assistant
        </h1>
        <p className="text-gray-500 max-w-lg mx-auto">
          Upload a candidate's resume to begin. Our agent will analyze the document, extract skills, and answer your questions with verified source attribution.
        </p>
      </div>
      <ResumeUpload />
    </main>
  );
}
