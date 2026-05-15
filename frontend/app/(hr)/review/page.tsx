"use client";

import Link from "next/link";
import { ClipboardList, FileText, Clock } from "lucide-react";
import { useReviewQueue } from "@/lib/api/hooks";

const SOURCE_LABEL: Record<string, string> = {
  pdf: "PDF Upload",
  text: "Text Paste",
  linkedin: "LinkedIn",
};

export default function ReviewQueuePage() {
  const { data: queue, isLoading } = useReviewQueue();

  return (
    <div className="px-8 py-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">Review Queue</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          AI-extracted profiles awaiting HR review before going live.
        </p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 rounded-xl border border-[var(--color-border)] bg-white animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && (!queue || queue.length === 0) && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-14 text-center">
          <ClipboardList className="h-10 w-10 text-[var(--color-muted-foreground)] mx-auto mb-3 opacity-40" />
          <p className="text-sm font-medium text-[var(--color-foreground)]">All caught up!</p>
          <p className="text-xs text-[var(--color-muted-foreground)] mt-1">
            No pending reviews. New submissions will appear here automatically.
          </p>
        </div>
      )}

      {queue && queue.length > 0 && (
        <div className="space-y-3">
          {queue.map((item) => (
            <Link
              key={item.upload_id}
              href={`/review/${item.upload_id}`}
              className="flex items-center gap-4 rounded-xl border border-[var(--color-border)] bg-white p-4 hover:shadow-md transition-shadow"
            >
              <div className="h-10 w-10 rounded-lg bg-purple-50 flex items-center justify-center shrink-0">
                <FileText className="h-5 w-5 text-purple-600" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold truncate">{item.candidate_name}</p>
                  <span className="shrink-0 rounded-full border border-[var(--color-border)] px-2 py-0.5 text-[10px] text-[var(--color-muted-foreground)]">
                    {SOURCE_LABEL[item.source] ?? item.source}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-0.5 text-xs text-[var(--color-muted-foreground)]">
                  <span>{item.skill_count} skills extracted</span>
                  {item.inferred_count > 0 && (
                    <span className="text-purple-600">✨ {item.inferred_count} inferred</span>
                  )}
                </div>
              </div>

              <div className="shrink-0 flex items-center gap-1.5 text-xs text-[var(--color-muted-foreground)]">
                <Clock className="h-3.5 w-3.5" />
                {new Date(item.created_at).toLocaleDateString()}
              </div>

              <span className="shrink-0 rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-medium text-amber-700">
                Pending
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
