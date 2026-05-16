"use client";

import Link from "next/link";
import type { Route } from "next";
import { useEffect, useState } from "react";
import { Users, ClipboardList, Search, TrendingUp, Clock, CheckCircle, AlertTriangle } from "lucide-react";
import { useEmployees, useReviewQueue, useSkillGaps } from "@/lib/api/hooks";
import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

const AVAILABILITY_COLOR: Record<string, string> = {
  available: "bg-gradient-to-r from-emerald-400 to-emerald-500",
  partial:   "bg-gradient-to-r from-amber-400 to-amber-500",
  allocated: "bg-gradient-to-r from-slate-300 to-slate-400",
};

export default function DashboardPage() {
  const { data: employees, isLoading: loadingEmp } = useEmployees();
  const { data: queue, isLoading: loadingQueue } = useReviewQueue();
  const { data: gaps } = useSkillGaps();
  const [barsVisible, setBarsVisible] = useState(false);

  const total     = employees?.length ?? 0;
  const available = employees?.filter((e) => e.availability === "available").length ?? 0;
  const partial   = employees?.filter((e) => e.availability === "partial").length ?? 0;
  const pending   = queue?.length ?? 0;
  const recentQueue = queue?.slice(0, 5) ?? [];

  // Trigger bar animation after data loads
  useEffect(() => {
    if (employees) {
      const t = setTimeout(() => setBarsVisible(true), 200);
      return () => clearTimeout(t);
    }
  }, [employees]);

  return (
    <div className="px-4 sm:px-8 py-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-[var(--color-border)] animate-fade-up">
        <div className="w-10 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full mb-3" />
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          Overview of your talent pool and pending reviews.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-8 stagger-children">
        {loadingEmp || loadingQueue ? (
          <>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton h-28 rounded-xl" />
            ))}
          </>
        ) : (
          <>
            <StatCard
              icon={<Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
              label="Total Employees" value={total}
              bg="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/20"
              accent="border-l-blue-500"
            />
            <StatCard
              icon={<CheckCircle className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />}
              label="Available Now" value={available}
              bg="bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900/30 dark:to-emerald-800/20"
              accent="border-l-emerald-500"
              sub={total ? `${Math.round((available / total) * 100)}% of team` : undefined}
            />
            <StatCard
              icon={<Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />}
              label="Partially Free" value={partial}
              bg="bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-900/30 dark:to-amber-800/20"
              accent="border-l-amber-500"
            />
            <StatCard
              icon={<ClipboardList className="h-5 w-5 text-purple-600 dark:text-purple-400" />}
              label="Pending Reviews" value={pending}
              bg="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/20"
              accent="border-l-purple-500"
              href="/review"
            />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Availability breakdown */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 shadow-sm animate-fade-up" style={{ animationDelay: "100ms" }}>
          <h2 className="text-sm font-semibold mb-5">Availability Breakdown</h2>
          {loadingEmp ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-8" />)}
            </div>
          ) : total === 0 ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">No employees yet.</p>
          ) : (
            <div className="space-y-4">
              {[
                { label: "Available",           key: "available", count: available,                    pct: (available / total) * 100 },
                { label: "Partially available", key: "partial",   count: partial,                      pct: (partial / total) * 100 },
                { label: "Fully allocated",     key: "allocated", count: total - available - partial,  pct: ((total - available - partial) / total) * 100 },
              ].map(({ label, key, count, pct }) => (
                <div key={key}>
                  <div className="flex justify-between text-xs mb-2">
                    <span className="font-medium">{label}</span>
                    <span className="text-[var(--color-muted-foreground)] tabular-nums">{count} · {Math.round(pct)}%</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-[var(--color-muted)] overflow-hidden">
                    <div
                      className={`h-full rounded-full ${AVAILABILITY_COLOR[key]}`}
                      style={{
                        width: barsVisible ? `${pct}%` : "0%",
                        transition: "width 0.8s cubic-bezier(0.4,0,0.2,1)",
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent review queue */}
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 shadow-sm animate-fade-up" style={{ animationDelay: "160ms" }}>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-semibold">Pending Reviews</h2>
            {pending > 0 && (
              <Link href="/review" className="text-xs font-medium text-[var(--color-primary)] hover:underline">
                View all →
              </Link>
            )}
          </div>
          {loadingQueue ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-12" />)}
            </div>
          ) : recentQueue.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-6 text-center">
              <CheckCircle className="h-8 w-8 text-emerald-500 mb-2 opacity-60" />
              <p className="text-sm font-medium">All caught up!</p>
              <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">No pending reviews.</p>
            </div>
          ) : (
            <ul className="space-y-1">
              {recentQueue.map((item) => (
                <li key={item.upload_id}>
                  <Link
                    href={`/review/${item.upload_id}` as Route}
                    className="flex items-center justify-between rounded-lg px-3 py-2.5 hover:bg-[var(--color-muted)] transition-colors group"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate group-hover:text-[var(--color-primary)] transition-colors">
                        {item.candidate_name}
                      </p>
                      <p className="text-xs text-[var(--color-muted-foreground)]">
                        {item.skill_count} skills · {item.inferred_count} inferred
                      </p>
                    </div>
                    <span className="shrink-0 ml-2 text-xs text-[var(--color-muted-foreground)]">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Skill Gap Teaser */}
      {gaps && (
        <div className="mt-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 shadow-sm animate-fade-up" style={{ animationDelay: "220ms" }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
              </div>
              <h2 className="text-sm font-semibold">Skill Gap Analysis</h2>
            </div>
            <Link href="/skill-gaps" className="text-xs font-medium text-[var(--color-primary)] hover:underline">
              View full report →
            </Link>
          </div>

          {/* Three summary stats */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label: "Critical", count: gaps.items.filter(g => g.gap_severity === "critical").length, color: "text-red-600 dark:text-red-400", bg: "bg-red-50 dark:bg-red-900/20", bar: "bg-red-500" },
              { label: "Low coverage", count: gaps.items.filter(g => g.gap_severity === "warning").length, color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-50 dark:bg-amber-900/20", bar: "bg-amber-400" },
              { label: "Healthy", count: gaps.items.filter(g => g.gap_severity === "healthy").length, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-900/20", bar: "bg-emerald-500" },
            ].map(({ label, count, color, bg, bar }) => (
              <div key={label} className={cn("rounded-lg p-3 text-center", bg)}>
                <p className={cn("text-xl font-bold tabular-nums", color)}>{count}</p>
                <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          {/* Top critical skills preview */}
          {gaps.items.filter(g => g.gap_severity === "critical").slice(0, 5).length > 0 && (
            <div>
              <p className="text-xs text-[var(--color-muted-foreground)] mb-2">Most critical gaps:</p>
              <div className="flex flex-wrap gap-1.5">
                {gaps.items.filter(g => g.gap_severity === "critical").slice(0, 6).map(g => (
                  <span key={g.name} className="rounded-full border border-red-200 bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700">
                    {g.name}
                  </span>
                ))}
                {gaps.items.filter(g => g.gap_severity === "critical").length > 6 && (
                  <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-muted)] px-2.5 py-0.5 text-xs text-[var(--color-muted-foreground)]">
                    +{gaps.items.filter(g => g.gap_severity === "critical").length - 6} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quick actions */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-up" style={{ animationDelay: "280ms" }}>
        <Link
          href="/search"
          className="group flex items-center gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 hover:shadow-lg hover:border-indigo-200 dark:hover:border-indigo-800 transition-all duration-200 shadow-sm"
        >
          <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-200">
            <Search className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold group-hover:text-[var(--color-primary)] transition-colors">Talent Search</p>
            <p className="text-xs text-[var(--color-muted-foreground)]">Ask in plain English — get ranked candidates</p>
          </div>
        </Link>
        <Link
          href="/employees"
          className="group flex items-center gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 hover:shadow-lg hover:border-emerald-200 dark:hover:border-emerald-800 transition-all duration-200 shadow-sm"
        >
          <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-200">
            <TrendingUp className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold group-hover:text-[var(--color-primary)] transition-colors">Employee Directory</p>
            <p className="text-xs text-[var(--color-muted-foreground)]">Browse and filter your talent pool</p>
          </div>
        </Link>
      </div>
    </div>
  );
}

function StatCard({
  icon, label, value, bg, accent, sub, href,
}: {
  icon: React.ReactNode; label: string; value: number;
  bg: string; accent: string;
  sub?: string; href?: Route;
}) {
  const inner = (
    <div className={cn(
      "rounded-xl border border-[var(--color-border)] border-l-4 bg-[var(--color-card)] p-4 h-full",
      "hover:shadow-lg transition-all duration-200 shadow-sm group cursor-default min-h-[130px]",
      accent,
    )}>
      <div className={cn("inline-flex h-10 w-10 items-center justify-center rounded-xl mb-3", bg)}>
        {icon}
      </div>
      <p className="text-2xl font-bold tracking-tight animate-count-up">{value}</p>
      <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5 font-medium">{label}</p>
      {sub && <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 font-semibold">{sub}</p>}
    </div>
  );
  return href ? (
    <Link href={href} className="block hover:scale-[1.02] transition-transform duration-150 h-full">{inner}</Link>
  ) : (
    <div className="hover:scale-[1.02] transition-transform duration-150 h-full">{inner}</div>
  );
}
