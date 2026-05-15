"use client";

import { MapPin, Briefcase, Calendar, FolderOpen, Award, Sparkles } from "lucide-react";
import { useMyEmployee } from "@/lib/api/hooks";
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

export default function ProfilePage() {
  const { data: emp, isLoading } = useMyEmployee();

  if (isLoading) {
    return (
      <div className="px-8 py-8 max-w-3xl mx-auto space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-28 rounded-xl border border-[var(--color-border)] bg-white animate-pulse" />
        ))}
      </div>
    );
  }

  if (!emp) {
    return (
      <div className="px-8 py-8 max-w-3xl mx-auto">
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-14 text-center">
          <Sparkles className="h-10 w-10 text-[var(--color-muted-foreground)] mx-auto mb-3 opacity-40" />
          <p className="text-sm font-medium">No profile yet</p>
          <p className="text-xs text-[var(--color-muted-foreground)] mt-1">
            Upload your resume and wait for HR to approve your profile.
          </p>
        </div>
      </div>
    );
  }

  const skillsByCategory = CATEGORY_ORDER.reduce<Record<string, typeof emp.skills>>((acc, cat) => {
    const s = emp.skills.filter((sk) => sk.category === cat);
    if (s.length) acc[cat] = s;
    return acc;
  }, {});

  const inferredCount = emp.skills.filter((s) => s.source === "inferred").length;

  return (
    <div className="px-8 py-8 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">My Profile</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          Your AI-extracted skill profile as visible to HR.
        </p>
      </div>

      {/* Hero */}
      <div className="rounded-xl border border-[var(--color-border)] bg-white p-6 mb-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-full bg-[var(--color-primary)] flex items-center justify-center text-white text-xl font-bold shrink-0">
              {emp.name[0]}
            </div>
            <div>
              <h2 className="text-lg font-semibold">{emp.name}</h2>
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
            "shrink-0 rounded-full border px-3 py-1 text-xs font-medium",
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
      </div>

      {/* Skills */}
      {Object.keys(skillsByCategory).length > 0 && (
        <div className="rounded-xl border border-[var(--color-border)] bg-white p-5 mb-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold">Skills</h2>
            {inferredCount > 0 && (
              <span className="text-xs text-purple-600 flex items-center gap-1">
                <Sparkles className="h-3.5 w-3.5" />
                {inferredCount} AI-inferred
              </span>
            )}
          </div>
          <div className="space-y-4">
            {Object.entries(skillsByCategory).map(([cat, skills]) => (
              <div key={cat}>
                <p className="text-xs text-[var(--color-muted-foreground)] font-medium uppercase tracking-wide mb-2">
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
        <div className="rounded-xl border border-[var(--color-border)] bg-white p-5 mb-5">
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <FolderOpen className="h-4 w-4 text-[var(--color-muted-foreground)]" />
            Projects
          </h2>
          <div className="space-y-3">
            {emp.projects.map((p) => (
              <div key={p.id} className="rounded-lg border border-[var(--color-border)] p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium">{p.name}</p>
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
        <div className="rounded-xl border border-[var(--color-border)] bg-white p-5">
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <Award className="h-4 w-4 text-[var(--color-muted-foreground)]" />
            Certifications
          </h2>
          <ul className="space-y-2">
            {emp.certifications.map((c) => (
              <li key={c.id} className="flex items-center justify-between text-sm">
                <div>
                  <span className="font-medium">{c.name}</span>
                  {c.issuer && <span className="text-[var(--color-muted-foreground)] ml-2">· {c.issuer}</span>}
                </div>
                {c.year && <span className="text-xs text-[var(--color-muted-foreground)]">{c.year}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
