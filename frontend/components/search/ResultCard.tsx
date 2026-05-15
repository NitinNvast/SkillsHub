"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, ChevronUp, MapPin, Briefcase } from "lucide-react";
import { ScoreRing } from "./ScoreRing";
import { SkillChip } from "@/components/skills/SkillChip";
import type { SearchResult } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

const AVAILABILITY_STYLE: Record<string, string> = {
  available: "bg-emerald-50 text-emerald-700",
  partial:   "bg-amber-50 text-amber-700",
  allocated: "bg-slate-100 text-slate-600",
};

export function ResultCard({ result, rank }: { result: SearchResult; rank: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        {/* Rank + score */}
        <div className="flex flex-col items-center gap-1">
          <span className="text-xs text-[var(--color-muted-foreground)] font-medium">#{rank}</span>
          <ScoreRing score={result.match_score} />
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <Link
                href={`/employees/${result.employee_id}`}
                className="text-base font-semibold hover:text-[var(--color-primary)] transition-colors"
              >
                {result.name}
              </Link>
              <div className="flex flex-wrap items-center gap-2 mt-0.5 text-sm text-[var(--color-muted-foreground)]">
                {result.title && (
                  <span className="flex items-center gap-1">
                    <Briefcase className="h-3.5 w-3.5" />
                    {result.title}
                  </span>
                )}
                {result.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {result.location}
                  </span>
                )}
              </div>
            </div>
            <span
              className={cn(
                "shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium",
                AVAILABILITY_STYLE[result.availability] ?? AVAILABILITY_STYLE.allocated,
              )}
            >
              {result.availability === "available" ? "Available" :
               result.availability === "partial"   ? "Partially available" :
               "Allocated"}
            </span>
          </div>

          {/* AI reasoning — the money shot */}
          <p className="mt-3 text-sm leading-relaxed text-[var(--color-foreground)]">
            {result.reasoning}
          </p>

          {/* Top skills */}
          {result.top_skills.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {result.top_skills.map((s) => (
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
          )}

          {/* Expand for strengths + gaps */}
          {(result.strengths.length > 0 || result.gaps.length > 0) && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="mt-3 flex items-center gap-1 text-xs text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors"
            >
              {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              {expanded ? "Hide details" : "Show strengths & gaps"}
            </button>
          )}

          {expanded && (
            <div className="mt-3 grid grid-cols-2 gap-4 text-xs">
              {result.strengths.length > 0 && (
                <div>
                  <p className="font-medium text-emerald-700 mb-1.5">Strengths</p>
                  <ul className="space-y-1">
                    {result.strengths.map((s, i) => (
                      <li key={i} className="flex gap-1.5 text-[var(--color-foreground)]">
                        <span className="text-emerald-500 mt-px">✓</span>{s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.gaps.length > 0 && (
                <div>
                  <p className="font-medium text-amber-700 mb-1.5">Gaps</p>
                  <ul className="space-y-1">
                    {result.gaps.map((g, i) => (
                      <li key={i} className="flex gap-1.5 text-[var(--color-foreground)]">
                        <span className="text-amber-500 mt-px">△</span>{g}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
