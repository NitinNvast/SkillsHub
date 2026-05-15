"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Check, X, Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import Link from "next/link";
import { useReviewDetail, useApprove, useReject } from "@/lib/api/hooks";
import { SkillChip } from "@/components/skills/SkillChip";

export default function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data, isLoading, error } = useReviewDetail(id);
  const { mutate: approve, isPending: approving } = useApprove();
  const { mutate: reject, isPending: rejecting } = useReject();
  const [showRaw, setShowRaw] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectForm, setShowRejectForm] = useState(false);

  function handleApprove() {
    approve(id, {
      onSuccess: () => router.push("/review"),
    });
  }

  function handleReject() {
    reject({ uploadId: id, reason: rejectReason || undefined }, {
      onSuccess: () => router.push("/review"),
    });
  }

  if (isLoading) {
    return (
      <div className="px-8 py-8 max-w-4xl mx-auto space-y-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 rounded-xl border border-[var(--color-border)] bg-white animate-pulse" />
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="px-8 py-8 max-w-4xl mx-auto">
        <p className="text-sm text-red-600">Could not load review details.</p>
      </div>
    );
  }

  const profile = data.current_profile;
  const extracted = data.extracted_payload as Record<string, unknown> | null;

  return (
    <div className="px-8 py-8 max-w-4xl mx-auto">
      {/* Back nav */}
      <Link href="/review" className="inline-flex items-center gap-1.5 text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] mb-6 transition-colors">
        <ArrowLeft className="h-4 w-4" />
        Back to queue
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-semibold">{profile?.name ?? "Unknown candidate"}</h1>
          <p className="text-sm text-[var(--color-muted-foreground)] mt-0.5">
            {profile?.title} {profile?.location ? `· ${profile.location}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {!showRejectForm ? (
            <>
              <button
                onClick={() => setShowRejectForm(true)}
                className="flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100 transition"
              >
                <X className="h-4 w-4" /> Reject
              </button>
              <button
                onClick={handleApprove}
                disabled={approving}
                className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60 transition"
              >
                <Check className="h-4 w-4" />
                {approving ? "Approving…" : "Approve & Publish"}
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <input
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Optional reason…"
                className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
              />
              <button
                onClick={handleReject}
                disabled={rejecting}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60 transition"
              >
                {rejecting ? "Rejecting…" : "Confirm Reject"}
              </button>
              <button
                onClick={() => setShowRejectForm(false)}
                className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] transition"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="space-y-5">
        {/* Profile summary */}
        {profile?.summary && (
          <Section title="Summary">
            <p className="text-sm leading-relaxed text-[var(--color-foreground)]">{profile.summary}</p>
          </Section>
        )}

        {/* Skills */}
        {profile?.skills && profile.skills.length > 0 && (
          <Section title="Skills">
            <div className="flex flex-wrap gap-1.5">
              {profile.skills.map((s) => (
                <SkillChip
                  key={s.id}
                  name={s.name}
                  category={s.category}
                  proficiency={s.proficiency}
                  years={s.years}
                  inferred={s.source === "inferred"}
                />
              ))}
            </div>
            {data.inferred_skills.length > 0 && (
              <p className="mt-2 text-xs text-purple-600 flex items-center gap-1">
                <Sparkles className="h-3.5 w-3.5" />
                {data.inferred_skills.length} skills were AI-inferred from project context
              </p>
            )}
          </Section>
        )}

        {/* Projects */}
        {profile?.projects && profile.projects.length > 0 && (
          <Section title="Projects">
            <div className="space-y-3">
              {profile.projects.map((p) => (
                <div key={p.id} className="rounded-lg border border-[var(--color-border)] p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">{p.name}</p>
                    {p.role && <span className="text-xs text-[var(--color-muted-foreground)]">{p.role}</span>}
                  </div>
                  {p.description && (
                    <p className="mt-1 text-xs text-[var(--color-muted-foreground)] leading-relaxed">{p.description}</p>
                  )}
                  {p.technologies.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {p.technologies.map((t) => (
                        <span key={t} className="rounded bg-[var(--color-muted)] px-1.5 py-0.5 text-[10px] text-[var(--color-muted-foreground)]">{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Certifications */}
        {profile?.certifications && profile.certifications.length > 0 && (
          <Section title="Certifications">
            <ul className="space-y-1">
              {profile.certifications.map((c) => (
                <li key={c.id} className="text-sm">
                  <span className="font-medium">{c.name}</span>
                  {c.issuer && <span className="text-[var(--color-muted-foreground)]"> · {c.issuer}</span>}
                  {c.year && <span className="text-[var(--color-muted-foreground)]"> · {c.year}</span>}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Raw text toggle */}
        {data.raw_text_preview && (
          <div className="rounded-xl border border-[var(--color-border)] bg-white">
            <button
              onClick={() => setShowRaw((v) => !v)}
              className="flex w-full items-center justify-between px-5 py-3 text-sm font-medium"
            >
              Raw Resume Text
              {showRaw ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
            {showRaw && (
              <div className="border-t border-[var(--color-border)] px-5 py-4">
                <pre className="text-xs text-[var(--color-muted-foreground)] whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">
                  {data.raw_text_preview}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-white p-5">
      <h2 className="text-sm font-semibold mb-3 text-[var(--color-foreground)]">{title}</h2>
      {children}
    </div>
  );
}
