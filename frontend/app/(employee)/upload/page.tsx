"use client";

import { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useUploadResume, useUploadText } from "@/lib/api/hooks";

type Tab = "pdf" | "text";

const TAB_LABELS: Record<Tab, string> = { pdf: "PDF Resume", text: "Paste Text" };

const WHAT_NEXT_STEPS = [
  "Claude AI extracts skills, projects, and certifications",
  "AI infers additional skills from your project descriptions",
  "HR reviews and approves your profile",
  "Your profile becomes searchable for project assignments",
];

export default function UploadPage() {
  const [tab, setTab] = useState<Tab>("pdf");
  const [text, setText] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { mutate: uploadPdf, isPending: uploadingPdf, data: pdfResult, error: pdfError, reset: resetPdf } = useUploadResume();
  const { mutate: uploadText, isPending: uploadingText, data: textResult, error: textError, reset: resetText } = useUploadText();

  const isPending = uploadingPdf || uploadingText;
  const result    = pdfResult ?? textResult;
  const error     = pdfError ?? textError;

  function handleFile(file: File) {
    if (!file.name.endsWith(".pdf")) return;
    const fd = new FormData();
    fd.append("file", file);
    uploadPdf(fd, {
      onSuccess: () => toast.success("Resume submitted! AI is extracting your skills."),
      onError: (err) => toast.error(err.message || "Resume upload failed. Please try again."),
    });
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleTextSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    uploadText({ text: text.trim() }, {
      onSuccess: () => toast.success("Resume submitted! AI is extracting your skills."),
      onError: (err) => toast.error(err.message || "Resume upload failed. Please try again."),
    });
  }

  function reset() {
    resetPdf();
    resetText();
    setText("");
  }

  if (result) {
    return (
      <div className="px-4 sm:px-8 py-8 max-w-xl mx-auto">
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 dark:bg-emerald-900/20 dark:border-emerald-800/50 p-8 text-center shadow-sm animate-scale-in">
          {/* Celebratory icon with ring */}
          <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-emerald-100 dark:bg-emerald-900/40 ring-4 ring-emerald-500/20 mb-4">
            <CheckCircle className="h-16 w-16 text-emerald-600 dark:text-emerald-400" />
          </div>
          <h2 className="text-lg font-bold text-emerald-900 dark:text-emerald-200">Resume submitted!</h2>
          <p className="text-sm text-emerald-700 dark:text-emerald-300 mt-2 leading-relaxed">
            Your resume is being processed by AI. An HR team member will review and approve it shortly.
          </p>
          <div className="mt-4 rounded-lg bg-white dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/50 px-4 py-3 text-left text-sm space-y-1 shadow-sm">
            <div className="flex justify-between">
              <span className="text-[var(--color-muted-foreground)]">Upload ID</span>
              <span className="font-mono text-xs">{result.upload_id.slice(0, 8)}…</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-muted-foreground)]">Status</span>
              <span className="text-amber-600 dark:text-amber-400 font-semibold">Pending review</span>
            </div>
          </div>
          <p className="mt-4 text-xs text-emerald-600 dark:text-emerald-400 flex items-center justify-center gap-1">
            <Sparkles className="h-3.5 w-3.5" />
            AI is extracting and inferring skills from your profile
          </p>
          <button
            onClick={reset}
            className="mt-6 text-sm text-emerald-700 dark:text-emerald-400 hover:underline cursor-pointer"
          >
            Upload another resume
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-8 py-8 max-w-xl mx-auto animate-fade-up">
      <div className="mb-8 pb-6 border-b border-[var(--color-border)]">
        <div className="w-8 h-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full mb-3" />
        <h1 className="text-2xl font-bold">Upload Resume</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          Our AI will extract your skills, experience, and projects automatically.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg bg-[var(--color-muted)] p-1 mb-6">
        {(["pdf", "text"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 rounded-md py-1.5 text-sm font-medium transition-colors cursor-pointer ${
              tab === t
                ? "bg-[var(--color-card)] text-[var(--color-foreground)] shadow-sm"
                : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
            }`}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {tab === "pdf" && (
        <div>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`group cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
              dragOver
                ? "border-[var(--color-primary)] bg-indigo-50 dark:bg-indigo-900/20 shadow-lg shadow-indigo-500/20 scale-[1.02]"
                : "border-[var(--color-border)] bg-[var(--color-card)] hover:border-[var(--color-primary)] hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 hover:shadow-md"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
            />
            {isPending ? (
              <div className="space-y-3">
                <div className="flex justify-center">
                  <Sparkles className="h-10 w-10 text-[var(--color-primary)] animate-pulse" />
                </div>
                <p className="text-sm font-semibold">AI is extracting skills…</p>
                {/* Animated progress bar */}
                <div className="w-full max-w-xs mx-auto h-1.5 bg-[var(--color-muted)] rounded-full overflow-hidden">
                  <div className="h-full w-1/3 bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full animate-[shimmer_1.5s_infinite]" style={{ backgroundSize: "200% 100%" }} />
                </div>
                <p className="text-xs text-[var(--color-muted-foreground)]">Extracting skills… This may take 15–30 seconds</p>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex justify-center">
                  <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-50 to-blue-100 dark:from-indigo-900/30 dark:to-blue-900/20 mb-3 group-hover:scale-110 transition-transform duration-200">
                    <Upload className="h-8 w-8 text-indigo-500" />
                  </div>
                </div>
                <p className="text-sm font-semibold mt-2">Drop your PDF here or click to browse</p>
                <p className="text-xs text-[var(--color-muted-foreground)]">PDF files only · Max 10 MB</p>
                {/* Supported format badge */}
                <div className="inline-flex items-center gap-1.5 mt-2 rounded-full border border-[var(--color-border)] bg-[var(--color-muted)] px-3 py-1 text-[10px] font-semibold text-[var(--color-muted-foreground)]">
                  <FileText className="h-3 w-3" />
                  PDF only
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === "text" && (
        <form onSubmit={handleTextSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1.5">
              Paste resume text
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste your resume, LinkedIn summary, or any structured work history here…"
              rows={14}
              className="w-full resize-none rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition shadow-sm"
            />
          </div>
          <button
            type="submit"
            disabled={isPending || !text.trim()}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-indigo-600 py-2.5 text-sm font-semibold text-white hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-60 transition cursor-pointer"
          >
            {isPending ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                AI is extracting skills…
              </>
            ) : (
              <>
                <FileText className="h-4 w-4" />
                Extract Skills with AI
              </>
            )}
          </button>
        </form>
      )}

      {error && (
        <div className="mt-4 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          {error.message}
        </div>
      )}

      {/* What happens next — timeline style */}
      <div className="mt-8 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 shadow-sm">
        <p className="text-xs font-semibold text-[var(--color-foreground)] mb-4">What happens after upload?</p>
        <div className="space-y-0">
          {WHAT_NEXT_STEPS.map((step, i) => {
            const isLast = i === WHAT_NEXT_STEPS.length - 1;
            return (
              <div key={i} className="flex gap-3">
                {/* Timeline left side */}
                <div className="flex flex-col items-center">
                  <div className="shrink-0 h-5 w-5 rounded-full bg-gradient-to-br from-indigo-500 to-indigo-600 text-white flex items-center justify-center font-bold z-10" style={{ fontSize: "9px" }}>
                    {i + 1}
                  </div>
                  {!isLast && (
                    <div className="w-px flex-1 bg-[var(--color-border)] mt-1 mb-1" style={{ minHeight: "16px" }} />
                  )}
                </div>
                {/* Step text */}
                <p className={`text-xs text-[var(--color-muted-foreground)] leading-snug ${isLast ? "" : "pb-4"}`}>
                  {step}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
