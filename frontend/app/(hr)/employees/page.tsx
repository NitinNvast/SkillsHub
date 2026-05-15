"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, MapPin, Briefcase } from "lucide-react";
import { useEmployees } from "@/lib/api/hooks";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

const AVAILABILITY_STYLE: Record<string, string> = {
  available: "bg-emerald-50 text-emerald-700 border-emerald-200",
  partial:   "bg-amber-50 text-amber-700 border-amber-200",
  allocated: "bg-slate-100 text-slate-600 border-slate-200",
};

const AVAILABILITY_LABEL: Record<string, string> = {
  available: "Available",
  partial:   "Partial",
  allocated: "Allocated",
};

export default function EmployeesPage() {
  const [q, setQ] = useState("");
  const { data: employees, isLoading } = useEmployees(q || undefined);

  return (
    <div className="px-4 sm:px-8 py-8 max-w-5xl mx-auto animate-fade-up">
      <div className="mb-8 pb-6 border-b border-[var(--color-border)]">
        <div className="w-8 h-0.5 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full mb-3" />
        <h1 className="text-2xl font-bold">Employee Directory</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          {employees ? `${employees.length} employees` : "Loading…"}
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-muted-foreground)]" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter by name, skill, or location…"
          className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] pl-9 pr-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition shadow-sm"
        />
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[...Array(6)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {!isLoading && employees?.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-muted-foreground)]">No employees found.</p>
        </div>
      )}

      {employees && employees.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-up stagger-children">
          {employees.map((emp) => (
            <Link
              key={emp.id}
              href={`/employees/${emp.id}`}
              className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 hover:shadow-lg hover:border-indigo-200 dark:hover:border-indigo-800 hover:-translate-y-0.5 transition-all duration-200 shadow-sm"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold truncate">{emp.name}</p>
                  <div className="flex flex-wrap items-center gap-2 mt-0.5 text-xs text-[var(--color-muted-foreground)]">
                    {emp.title && (
                      <span className="flex items-center gap-1">
                        <Briefcase className="h-3 w-3" />{emp.title}
                      </span>
                    )}
                    {emp.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />{emp.location}
                      </span>
                    )}
                  </div>
                </div>
                <span className={cn(
                  "shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-semibold",
                  AVAILABILITY_STYLE[emp.availability] ?? AVAILABILITY_STYLE.allocated,
                )}>
                  {AVAILABILITY_LABEL[emp.availability] ?? "Allocated"}
                </span>
              </div>

              {emp.top_skills.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {emp.top_skills.slice(0, 5).map((s) => (
                    <span
                      key={s}
                      className="rounded-full bg-[var(--color-muted)] px-2 py-0.5 text-[10px] text-[var(--color-muted-foreground)]"
                    >
                      {s}
                    </span>
                  ))}
                  {emp.top_skills.length > 5 && (
                    <span className="rounded-full bg-[var(--color-muted)] px-2 py-0.5 text-[10px] text-[var(--color-muted-foreground)]">
                      +{emp.top_skills.length - 5}
                    </span>
                  )}
                </div>
              )}

              {emp.total_years_exp != null && (
                <p className="mt-2 text-xs text-[var(--color-muted-foreground)]">
                  {emp.total_years_exp}y experience
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
