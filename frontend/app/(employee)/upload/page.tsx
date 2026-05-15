"use client";

import { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, Sparkles } from "lucide-react";
import { useUploadResume, useUploadText } from "@/lib/api/hooks";

type Tab = "pdf" | "text";

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
    uploadPdf(fd);
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
    uploadText({ text: text.trim() });
  }

  function reset() {
    resetPdf();
    resetText();
    setText("");
  }

  if (result) {
    return (
      <div className="px-8 py-8 max-w-xl mx-auto">
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-8 text-center">
          <CheckCircle className="h-12 w-12 text-emerald-600 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-emerald-900">Resume submitted!</h2>
          <p className="text-sm text-emerald-700 mt-2 leading-relaxed">
            Your resume is being processed by AI. An HR team member will review and approve it shortly.
          </p>
          <div className="mt-4 rounded-lg bg-white border border-emerald-200 px-4 py-3 text-left text-sm space-y-1">
            <div className="flex justify-between">
              <span className="text-[var(--color-muted-foreground)]">Upload ID</span>
              <span className="font-mono text-xs">{result.upload_id.slice(0, 8)}…</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-muted-foreground)]">Status</span>
              <span className="text-amber-600 font-medium">Pending review</span>
            </div>
          </div>
          <p className="mt-4 text-xs text-emerald-600 flex items-center justify-center gap-1">
            <Sparkles className="h-3.5 w-3.5" />
            AI is extracting and inferring skills from your profile
          </p>
          <button
            onClick={reset}
            className="mt-6 text-sm text-emerald-700 hover:underline"
          >
            Upload another resume
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-8 py-8 max-w-xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">Upload Resume</h1>
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
            className={`flex-1 rounded-md py-1.5 text-sm font-medium transition-colors ${
              tab === t
                ? "bg-white text-[var(--color-foreground)] shadow-sm"
                : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
            }`}
          >
            {t === "pdf" ? "PDF Upload" : "Paste Text"}
          </button>
        ))}
      </div>

      {tab === "pdf" ? (
        <div>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
              dragOver
                ? "border-[var(--color-primary)] bg-blue-50"
                : "border-[var(--color-border)] bg-white hover:border-[var(--color-primary)] hover:bg-blue-50/50"
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
                <p className="text-sm font-medium">AI is extracting skills…</p>
                <p className="text-xs text-[var(--color-muted-foreground)]">This may take 15–30 seconds</p>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex justify-center">
                  <Upload className="h-10 w-10 text-[var(--color-muted-foreground)]" />
                </div>
                <p className="text-sm font-medium">Drop your PDF here or click to browse</p>
                <p className="text-xs text-[var(--color-muted-foreground)]">PDF files only · Max 10 MB</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <form onSubmit={handleTextSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Paste resume text
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste your resume, LinkedIn summary, or any structured work history here…"
              rows={12}
              className="w-full resize-none rounded-xl border border-[var(--color-border)] bg-white px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition"
            />
          </div>
          <button
            type="submit"
            disabled={isPending || !text.trim()}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-[var(--color-primary)] py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60 transition"
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

      {/* What happens next */}
      <div className="mt-8 rounded-xl border border-[var(--color-border)] bg-[var(--color-muted)] p-4 space-y-2">
        <p className="text-xs font-medium text-[var(--color-foreground)]">What happens after upload?</p>
        {[
          "Claude AI extracts skills, projects, and certifications",
          "AI infers additional skills from your project descriptions",
          "HR reviews and approves your profile",
          "Your profile becomes searchable for project assignments",
        ].map((step, i) => (
          <div key={i} className="flex items-start gap-2 text-xs text-[var(--color-muted-foreground)]">
            <span className="shrink-0 h-4 w-4 rounded-full bg-[var(--color-primary)] text-white flex items-center justify-center font-medium" style={{ fontSize: "9px" }}>
              {i + 1}
            </span>
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}
