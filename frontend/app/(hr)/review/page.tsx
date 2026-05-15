"use client";

import Link from "next/link";
import { ClipboardList, FileText, Clock } from "lucide-react";
import { useReviewQueue } from "@/lib/api/hooks";
import { SkeletonTable } from "@/components/ui/Skeleton";

const SOURCE_LABEL: Record<string, string> = {
  pdf: "PDF Upload",
  text: "Text Paste",
  linkedin: "LinkedIn",
};

export default function ReviewQueuePage() {
  const { data: queue, isLoading } = useReviewQueue();

  return (
    <div className="px-4 sm:px-8 py-8 max-w-4xl mx-auto animate-fade-up">
      <div className="mb-8 pb-6 border-b border-[var(--color-border)]">
        <div className="w-8 h-0.5 bg-gradient-to-r from-amber-400 to-orange-400 rounded-full mb-3" />
        <h1 className="text-2xl font-bold">Review Queue</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          AI-extracted profiles awaiting HR review before going live.
        </p>
      </div>

      {isLoading && <SkeletonTable rows={4} />}

      {!isLoading && (!queue || queue.length === 0) && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-14 text-center">
          <ClipboardList className="h-10 w-10 text-[var(--color-muted-foreground)] mx-auto mb-3 opacity-40" />
          <p className="text-sm font-semibold text-[var(--color-foreground)]">All caught up!</p>
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
              className="group flex items-center gap-4 rounded-xl border border-[var(--color-border)] border-l-4 border-l-amber-400 bg-[var(--color-card)] p-4 hover:shadow-md transition-shadow shadow-sm"
            >
              <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-purple-50 to-purple-100 flex items-center justify-center shrink-0">
                <FileText className="h-5 w-5 text-purple-600" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold truncate group-hover:text-[var(--color-primary)] transition-colors">{item.candidate_name}</p>
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

              <span className="shrink-0 rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-xs font-semibold text-amber-700">
                Pending
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
