'use client';
import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, FileText, ChevronRight } from 'lucide-react';
import { ResumeSummary } from '@/lib/types';

export default function ResumeInsightsDrawer({ summary }: { summary: ResumeSummary }) {
  const [open, setOpen] = useState(false);

  if (!summary) return null;

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button className="flex items-center gap-2 bg-white/60 hover:bg-white/80 backdrop-blur-md px-4 py-2 rounded-full border border-white/50 shadow-sm transition-all text-sm font-medium text-text-primary">
          <FileText size={16} className="text-primary" />
          Resume Insights
          <ChevronRight size={16} className="text-text-secondary" />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white/90 backdrop-blur-xl border-l border-white/50 shadow-2xl z-50 p-6 overflow-y-auto data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right duration-300">
          <div className="flex justify-between items-center mb-6">
            <Dialog.Title className="text-xl font-bold text-text-primary">Candidate Insights</Dialog.Title>
            <Dialog.Close asChild>
              <button className="p-2 rounded-full hover:bg-gray-100 transition-colors text-text-secondary">
                <X size={20} />
              </button>
            </Dialog.Close>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
              <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-2">Name</h3>
              <p className="text-lg font-bold text-text-primary">{summary.name || 'Unknown Candidate'}</p>
            </div>

            <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
              <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3">Top Skills</h3>
              <div className="flex flex-wrap gap-2">
                {summary.skills.map((skill, i) => (
                  <span key={i} className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full font-medium">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            
            {/* Note: Additional fields like Experience and Education can be added here if available in the API response */}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
