"use client";

import Link from "next/link";
import { AlertCircle, ClipboardList, FileText, Clock } from "lucide-react";
import { useReviewQueue } from "@/lib/api/hooks";
import { SkeletonTable } from "@/components/ui/Skeleton";

const SOURCE_LABEL: Record<string, string> = {
  pdf: "PDF Upload",
  text: "Text Paste",
  linkedin: "LinkedIn",
};

function relativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const d = Math.floor(diff / 86400000);
  if (d === 0) return "today";
  if (d === 1) return "yesterday";
  return `${d}d ago`;
}

export default function ReviewQueuePage() {
  const { data: queue, isLoading, isError } = useReviewQueue();

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

      {isError && (
        <div className="flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Failed to load review queue.</p>
            <p className="text-xs mt-0.5 text-red-600">Check your connection or refresh the page.</p>
          </div>
        </div>
      )}

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
          {queue.map((item) => {
            const isFailed = item.status === "failed";
            return (
              <Link
                key={item.upload_id}
                href={`/review/${item.upload_id}`}
                className={`group flex items-center gap-4 rounded-xl border border-l-4 bg-[var(--color-card)] p-4 hover:shadow-md transition-shadow shadow-sm ${
                  isFailed
                    ? "border-[var(--color-border)] border-l-red-400"
                    : "border-[var(--color-border)] border-l-amber-400"
                }`}
              >
                <div className={`h-10 w-10 rounded-lg flex items-center justify-center shrink-0 ${
                  isFailed ? "bg-red-50" : "bg-gradient-to-br from-purple-50 to-purple-100"
                }`}>
                  <FileText className={`h-5 w-5 ${isFailed ? "text-red-500" : "text-purple-600"}`} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold truncate group-hover:text-[var(--color-primary)] transition-colors">{item.candidate_name}</p>
                    <span className="shrink-0 rounded-full border border-[var(--color-border)] px-2 py-0.5 text-[10px] text-[var(--color-muted-foreground)]">
                      {SOURCE_LABEL[item.source] ?? item.source}
                    </span>
                    {!isFailed && item.skill_count > 0 && (
                      <span className="shrink-0 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700 dark:border-amber-800/50 dark:bg-amber-900/20 dark:text-amber-400">
                        {item.skill_count} skills
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5 text-xs text-[var(--color-muted-foreground)]">
                    {isFailed ? (
                      <span className="text-red-500">Extraction failed — AI could not process this resume</span>
                    ) : (
                      <>
                        <span>{item.skill_count} skills extracted</span>
                        {item.inferred_count > 0 && (
                          <span className="text-purple-600">✨ {item.inferred_count} inferred</span>
                        )}
                      </>
                    )}
                  </div>
                </div>

                <div
                  className="shrink-0 flex items-center gap-1.5 text-xs text-[var(--color-muted-foreground)]"
                  title={new Date(item.created_at).toLocaleDateString()}
                >
                  <Clock className="h-3.5 w-3.5" />
                  {relativeTime(item.created_at)}
                </div>

                <span className={`shrink-0 rounded-full border px-3 py-1 text-xs font-semibold ${
                  isFailed
                    ? "bg-red-50 border-red-200 text-red-700"
                    : "bg-amber-50 border-amber-200 text-amber-700"
                }`}>
                  {isFailed ? "Failed" : "Pending"}
                </span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
