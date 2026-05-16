"use client";

import { useState } from "react";
import { Users2, Sparkles, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";
import { useTeamBuilder, type TeamMemberProposal } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

const DEMO_DESCRIPTIONS = [
  "Build a 4-person team for a 3-month fintech mobile app. Need React Native, Node.js backend, PostgreSQL, and a tech lead who can manage stakeholders.",
  "Healthcare patient portal rewrite. 6-person team, 6 months. Need frontend (React), backend (Java Spring Boot), DevOps (Kubernetes), and a UX-focused lead.",
  "Real-time analytics dashboard for e-commerce. 3 engineers, 8 weeks. Python data pipeline, React frontend, AWS infrastructure.",
];

function MemberCard({ member, rank }: { member: TeamMemberProposal; rank: number }) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="h-9 w-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold shrink-0">
          {rank}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div>
              <p className="text-sm font-semibold">{member.name}</p>
              {member.title && (
                <p className="text-xs text-[var(--color-muted-foreground)]">{member.title}</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-indigo-600">{member.match_score}% fit</span>
              <span className="rounded-full bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
                {member.role_in_project}
              </span>
            </div>
          </div>
          {member.top_skills.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {member.top_skills.map((s) => (
                <span
                  key={s}
                  className="rounded-full bg-[var(--color-muted)] px-2 py-0.5 text-[10px] text-[var(--color-muted-foreground)]"
                >
                  {s}
                </span>
              ))}
            </div>
          )}
          <p className="mt-2 text-xs text-[var(--color-muted-foreground)] leading-relaxed">
            {member.rationale}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function TeamBuilderPage() {
  const [description, setDescription] = useState("");
  const [teamSize, setTeamSize] = useState(4);
  const [durationWeeks, setDurationWeeks] = useState(8);
  const [showAlternatives, setShowAlternatives] = useState(false);

  const { mutate, data, isPending, error, reset } = useTeamBuilder();

  function handleBuild(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) return;
    mutate(
      { description: description.trim(), team_size: teamSize, duration_weeks: durationWeeks },
      {
        onError: (err) => toast.error(err.message || "Team composition failed. Please try again."),
      }
    );
  }

  return (
    <div className="px-4 sm:px-8 py-8 max-w-4xl mx-auto animate-fade-up">
      <div className="mb-8 pb-6 border-b border-[var(--color-border)]">
        <div className="w-8 h-0.5 bg-gradient-to-r from-violet-500 to-purple-500 rounded-full mb-3" />
        <h1 className="text-2xl font-bold">Team Builder</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          Describe your project and AI will compose the ideal team from your talent pool.
        </p>
      </div>

      <form onSubmit={handleBuild} className="space-y-5 mb-8">
        <div>
          <label className="block text-sm font-semibold mb-1.5">Project description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the project, tech stack, timeline, and any specific requirements…"
            rows={4}
            className="w-full resize-none rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition shadow-sm"
          />
        </div>

        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-semibold mb-1.5">Team size</label>
            <input
              type="number"
              min={2}
              max={8}
              value={teamSize}
              onChange={(e) => setTeamSize(Math.min(8, Math.max(2, parseInt(e.target.value) || 2)))}
              className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition shadow-sm"
            />
            <p className="text-xs text-[var(--color-muted-foreground)] mt-1">2–8 people</p>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-semibold mb-1.5">Duration (weeks)</label>
            <input
              type="number"
              min={1}
              max={52}
              value={durationWeeks}
              onChange={(e) => setDurationWeeks(Math.min(52, Math.max(1, parseInt(e.target.value) || 1)))}
              className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition shadow-sm"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isPending || !description.trim()}
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 py-2.5 text-sm font-semibold text-white hover:from-violet-600 hover:to-purple-700 disabled:opacity-60 transition cursor-pointer shadow-sm"
        >
          {isPending ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              AI is composing your team…
            </>
          ) : (
            <>
              <Users2 className="h-4 w-4" />
              Build Team with AI
            </>
          )}
        </button>
      </form>

      {/* Demo chips */}
      {!data && !isPending && (
        <div className="mb-8">
          <p className="text-xs text-[var(--color-muted-foreground)] mb-2">Try an example:</p>
          <div className="flex flex-col gap-2">
            {DEMO_DESCRIPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDescription(d)}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3 text-xs text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] hover:text-[var(--color-foreground)] transition text-left cursor-pointer shadow-sm"
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          {error.message}
        </div>
      )}

      {data && !isPending && (
        <div className="space-y-6 animate-fade-up">
          {/* Summary bar */}
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-4 w-4 text-violet-500" />
              <span className="text-xs font-semibold text-violet-600">AI Team Composition</span>
            </div>
            <p className="text-sm text-[var(--color-foreground)] leading-relaxed">
              {data.proposal.team_rationale}
            </p>
            <p className="mt-2 text-xs text-[var(--color-muted-foreground)]">
              Considered {data.total_candidates_considered} candidates · selected {data.proposal.team.length} members
            </p>
          </div>

          {/* Team members */}
          {data.proposal.team.length > 0 ? (
            <div>
              <h2 className="text-sm font-semibold mb-3">Proposed Team</h2>
              <div className="space-y-3">
                {data.proposal.team.map((m, i) => (
                  <MemberCard key={m.employee_id} member={m} rank={i + 1} />
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-[var(--color-border)] p-10 text-center">
              <p className="text-sm text-[var(--color-muted-foreground)]">
                No suitable team could be composed from the current talent pool.
              </p>
            </div>
          )}

          {/* Gaps */}
          {data.proposal.gaps.length > 0 && (
            <div className="rounded-xl border border-amber-100 bg-amber-50 p-4">
              <p className="text-xs font-semibold text-amber-800 mb-2">Skill gaps identified</p>
              <ul className="space-y-1">
                {data.proposal.gaps.map((g, i) => (
                  <li key={i} className="text-xs text-amber-700 flex items-start gap-1.5">
                    <span className="shrink-0 mt-0.5">•</span>
                    {g}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Alternatives */}
          {data.proposal.alternatives.length > 0 && (
            <div>
              <button
                onClick={() => setShowAlternatives(!showAlternatives)}
                className="flex items-center gap-2 text-sm font-semibold text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition cursor-pointer"
              >
                {showAlternatives ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                {data.proposal.alternatives.length} alternative{data.proposal.alternatives.length > 1 ? "s" : ""} available
              </button>
              {showAlternatives && (
                <div className="mt-3 space-y-3">
                  {data.proposal.alternatives.map((m, i) => (
                    <MemberCard key={m.employee_id} member={m} rank={i + 1} />
                  ))}
                </div>
              )}
            </div>
          )}

          <button
            onClick={reset}
            className="text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition"
          >
            ← Start over
          </button>
        </div>
      )}
    </div>
  );
}
