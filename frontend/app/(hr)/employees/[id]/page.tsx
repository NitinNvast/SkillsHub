"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, MapPin, Briefcase, Calendar, FolderOpen, Award, GithubIcon } from "lucide-react";
import { toast } from "sonner";
import { useEmployee, useGitHubSync } from "@/lib/api/hooks";
import { SkillChip } from "@/components/skills/SkillChip";
import { cn } from "@/lib/utils";

const AVAILABILITY_STYLE: Record<string, string> = {
  available: "bg-emerald-50 text-emerald-700 border-emerald-200",
  partial:   "bg-amber-50 text-amber-700 border-amber-200",
  allocated: "bg-slate-100 text-slate-600 border-slate-200",
};

const AVAILABILITY_LABEL: Record<string, string> = {
  available: "Available",
  partial:   "Partially Available",
  allocated: "Fully Allocated",
};

const CATEGORY_ORDER = ["language", "framework", "platform", "tool", "domain"];

export default function EmployeeProfilePage() {
  const { id } = useParams<{ id: string }>();
  const { data: emp, isLoading, error } = useEmployee(id);
  const [githubInput, setGithubInput] = useState("");
  const { mutate: syncGitHub, isPending: syncingGitHub } = useGitHubSync(id);

  function handleGitHubSync(e: React.FormEvent) {
    e.preventDefault();
    if (!githubInput.trim()) return;
    syncGitHub(
      { github_username: githubInput.trim() },
      {
        onSuccess: () => {
          toast.success("GitHub skills synced successfully.");
          setGithubInput("");
        },
        onError: (err) => toast.error(err.message || "GitHub sync failed."),
      }
    );
  }

  if (isLoading) {
    return (
      <div className="px-8 py-8 max-w-4xl mx-auto space-y-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] animate-pulse" />
        ))}
      </div>
    );
  }

  if (error || !emp) {
    return (
      <div className="px-8 py-8 max-w-4xl mx-auto">
        <p className="text-sm text-red-600">Employee not found.</p>
      </div>
    );
  }

  const skillsByCategory = CATEGORY_ORDER.reduce<Record<string, typeof emp.skills>>((acc, cat) => {
    const s = emp.skills.filter((sk) => sk.category === cat);
    if (s.length) acc[cat] = s;
    return acc;
  }, {});

  return (
    <div className="px-8 py-8 max-w-4xl mx-auto">
      <Link
        href="/employees"
        className="inline-flex items-center gap-1.5 text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] mb-6 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to directory
      </Link>

      {/* Hero */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-6 mb-5 shadow-sm overflow-hidden">
        {/* Accent gradient strip */}
        <div className="h-1.5 rounded-t-xl bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-500 -mx-6 -mt-6 mb-5" />
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full ring-2 ring-indigo-300 dark:ring-indigo-700 bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold shrink-0">
              {emp.name[0]}
            </div>
            <div>
              <h1 className="text-xl font-bold">{emp.name}</h1>
              <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-[var(--color-muted-foreground)]">
                {emp.title && (
                  <span className="flex items-center gap-1">
                    <Briefcase className="h-3.5 w-3.5" />{emp.title}
                  </span>
                )}
                {emp.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />{emp.location}
                  </span>
                )}
                {emp.total_years_exp != null && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />{emp.total_years_exp}y experience
                  </span>
                )}
              </div>
            </div>
          </div>
          <span className={cn(
            "shrink-0 rounded-full border px-3 py-1 text-xs font-semibold",
            AVAILABILITY_STYLE[emp.availability] ?? AVAILABILITY_STYLE.allocated,
          )}>
            {AVAILABILITY_LABEL[emp.availability] ?? "Allocated"}
          </span>
        </div>

        {emp.summary && (
          <p className="mt-4 text-sm leading-relaxed text-[var(--color-foreground)] border-t border-[var(--color-border)] pt-4">
            {emp.summary}
          </p>
        )}

        {emp.current_project && (
          <div className="mt-3 flex items-center gap-1.5 text-sm">
            <span className="text-[var(--color-muted-foreground)]">Current project:</span>
            <span className="font-semibold">{emp.current_project}</span>
          </div>
        )}
      </div>

      {/* Skills by category */}
      {Object.keys(skillsByCategory).length > 0 && (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 mb-5 shadow-sm">
          <h2 className="text-sm font-semibold mb-4">Skills</h2>
          <div className="space-y-4">
            {Object.entries(skillsByCategory).map(([cat, skills]) => (
              <div key={cat}>
                <p className="text-xs text-[var(--color-muted-foreground)] font-semibold uppercase tracking-wide mb-2">
                  {cat}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {skills
                    .sort((a, b) => (b.years ?? 0) - (a.years ?? 0))
                    .map((s) => (
                      <SkillChip
                        key={s.id}
                        name={s.name}
                        category={s.category}
                        proficiency={s.proficiency}
                        years={s.years}
                        inferred={s.source === "inferred"}
                        fromGithub={s.source === "github"}
                      />
                    ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Projects */}
      {emp.projects.length > 0 && (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 mb-5 shadow-sm">
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <FolderOpen className="h-4 w-4 text-[var(--color-muted-foreground)]" />
            Projects
          </h2>
          <div className="space-y-3">
            {emp.projects.map((p) => (
              <div key={p.id} className="rounded-lg border border-[var(--color-border)] border-l-2 border-l-indigo-200 dark:border-l-indigo-800 bg-[var(--color-background)] p-4 pl-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold">{p.name}</p>
                    {p.role && <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">{p.role}</p>}
                  </div>
                  {(p.start_date || p.end_date) && (
                    <p className="shrink-0 text-xs text-[var(--color-muted-foreground)]">
                      {p.start_date ? new Date(p.start_date).getFullYear() : "?"}
                      {" – "}
                      {p.end_date ? new Date(p.end_date).getFullYear() : "Present"}
                    </p>
                  )}
                </div>
                {p.description && (
                  <p className="mt-2 text-xs text-[var(--color-muted-foreground)] leading-relaxed">{p.description}</p>
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
        </div>
      )}

      {/* Certifications */}
      {emp.certifications.length > 0 && (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 mb-5 shadow-sm">
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <Award className="h-4 w-4 text-[var(--color-muted-foreground)]" />
            Certifications
          </h2>
          <ul className="space-y-2">
            {emp.certifications.map((c) => (
              <li key={c.id} className="flex items-center justify-between text-sm">
                <div>
                  <span className="font-semibold">{c.name}</span>
                  {c.issuer && <span className="text-[var(--color-muted-foreground)] ml-2">· {c.issuer}</span>}
                </div>
                {c.year && <span className="text-xs text-[var(--color-muted-foreground)]">{c.year}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* GitHub Sync */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 shadow-sm">
        <h2 className="text-sm font-semibold mb-1 flex items-center gap-2">
          <GithubIcon className="h-4 w-4 text-[var(--color-muted-foreground)]" />
          Sync GitHub Skills
        </h2>
        <p className="text-xs text-[var(--color-muted-foreground)] mb-3">
          Infer active skills from public repos — languages, frameworks, and tools from recent commits.
        </p>
        <form onSubmit={handleGitHubSync} className="flex gap-2">
          <input
            value={githubInput}
            onChange={(e) => setGithubInput(e.target.value)}
            placeholder="GitHub username (e.g. octocat)"
            className="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
          />
          <button
            type="submit"
            disabled={syncingGitHub || !githubInput.trim()}
            className="flex items-center gap-1.5 rounded-lg bg-[var(--color-foreground)] text-[var(--color-background)] px-3 py-2 text-xs font-semibold disabled:opacity-50 transition cursor-pointer hover:opacity-80"
          >
            {syncingGitHub ? (
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current/30 border-t-current" />
            ) : (
              <GithubIcon className="h-3.5 w-3.5" />
            )}
            Sync
          </button>
        </form>
      </div>
    </div>
  );
}
