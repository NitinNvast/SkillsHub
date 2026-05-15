"use client";

import Link from "next/link";
import { Users, ClipboardList, Search, TrendingUp, Clock, CheckCircle, AlertTriangle } from "lucide-react";
import { useEmployees, useReviewQueue, useSkillGaps } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

const AVAILABILITY_COLOR: Record<string, string> = {
  available: "bg-emerald-500",
  partial:   "bg-amber-500",
  allocated: "bg-slate-400",
};

export default function DashboardPage() {
  const { data: employees } = useEmployees();
  const { data: queue } = useReviewQueue();
  const { data: gaps } = useSkillGaps();

  const total        = employees?.length ?? 0;
  const available    = employees?.filter((e) => e.availability === "available").length ?? 0;
  const partial      = employees?.filter((e) => e.availability === "partial").length ?? 0;
  const pending      = queue?.length ?? 0;

  const recentQueue  = queue?.slice(0, 5) ?? [];

  return (
    <div className="px-8 py-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          Overview of your talent pool and pending reviews.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Users className="h-5 w-5 text-blue-600" />}
          label="Total Employees"
          value={total}
          bg="bg-blue-50"
        />
        <StatCard
          icon={<CheckCircle className="h-5 w-5 text-emerald-600" />}
          label="Available Now"
          value={available}
          bg="bg-emerald-50"
          sub={total ? `${Math.round((available / total) * 100)}% of team` : undefined}
        />
        <StatCard
          icon={<Clock className="h-5 w-5 text-amber-600" />}
          label="Partially Free"
          value={partial}
          bg="bg-amber-50"
        />
        <StatCard
          icon={<ClipboardList className="h-5 w-5 text-purple-600" />}
          label="Pending Reviews"
          value={pending}
          bg="bg-purple-50"
          href="/review"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Availability breakdown */}
        <div className="rounded-xl border border-[var(--color-border)] bg-white p-5">
          <h2 className="text-sm font-semibold mb-4">Availability Breakdown</h2>
          {total === 0 ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">No employees yet.</p>
          ) : (
            <div className="space-y-3">
              {[
                { label: "Available",          key: "available", count: available    },
                { label: "Partially available", key: "partial",   count: partial      },
                { label: "Fully allocated",     key: "allocated", count: total - available - partial },
              ].map(({ label, key, count }) => (
                <div key={key}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-[var(--color-foreground)]">{label}</span>
                    <span className="text-[var(--color-muted-foreground)]">{count} people</span>
                  </div>
                  <div className="h-2 rounded-full bg-[var(--color-muted)] overflow-hidden">
                    <div
                      className={`h-full rounded-full ${AVAILABILITY_COLOR[key]}`}
                      style={{ width: `${total ? (count / total) * 100 : 0}%`, transition: "width 0.6s ease" }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent review queue */}
        <div className="rounded-xl border border-[var(--color-border)] bg-white p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold">Pending Reviews</h2>
            {pending > 0 && (
              <Link href="/review" className="text-xs text-[var(--color-primary)] hover:underline">
                View all →
              </Link>
            )}
          </div>
          {recentQueue.length === 0 ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">All caught up — no pending reviews.</p>
          ) : (
            <ul className="space-y-2">
              {recentQueue.map((item) => (
                <li key={item.upload_id}>
                  <Link
                    href={`/review/${item.upload_id}`}
                    className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-[var(--color-muted)] transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{item.candidate_name}</p>
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

      {/* Skill Gap Analysis */}
      {gaps && gaps.length > 0 && (
        <div className="mt-6 rounded-xl border border-[var(--color-border)] bg-white p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <h2 className="text-sm font-semibold">Skill Gap Analysis</h2>
            </div>
            <span className="text-xs text-[var(--color-muted-foreground)]">
              {gaps.filter(g => g.gap_severity !== "healthy").length} gaps identified
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
            {gaps.slice(0, 10).map((g) => (
              <div
                key={g.name}
                className={cn(
                  "rounded-lg border p-3 text-xs",
                  g.gap_severity === "critical" && "border-red-200 bg-red-50",
                  g.gap_severity === "warning"  && "border-amber-200 bg-amber-50",
                  g.gap_severity === "healthy"  && "border-emerald-200 bg-emerald-50",
                )}
              >
                <p className="font-medium truncate">{g.name}</p>
                <p className={cn(
                  "text-[10px] mt-0.5",
                  g.gap_severity === "critical" && "text-red-600",
                  g.gap_severity === "warning"  && "text-amber-600",
                  g.gap_severity === "healthy"  && "text-emerald-600",
                )}>
                  {g.employee_count === 0
                    ? "No coverage"
                    : `${g.employee_count} employee${g.employee_count !== 1 ? "s" : ""}${g.expert_count > 0 ? ` · ${g.expert_count} expert` : ""}`}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Link
          href="/search"
          className="flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-white p-4 hover:shadow-md transition-shadow"
        >
          <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center">
            <Search className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-medium">Talent Search</p>
            <p className="text-xs text-[var(--color-muted-foreground)]">Ask in plain English — get ranked candidates</p>
          </div>
        </Link>
        <Link
          href="/employees"
          className="flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-white p-4 hover:shadow-md transition-shadow"
        >
          <div className="h-10 w-10 rounded-lg bg-emerald-50 flex items-center justify-center">
            <TrendingUp className="h-5 w-5 text-emerald-600" />
          </div>
          <div>
            <p className="text-sm font-medium">Employee Directory</p>
            <p className="text-xs text-[var(--color-muted-foreground)]">Browse and filter your talent pool</p>
          </div>
        </Link>
      </div>
    </div>
  );
}

function StatCard({
  icon, label, value, bg, sub, href,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  bg: string;
  sub?: string;
  href?: string;
}) {
  const inner = (
    <div className="rounded-xl border border-[var(--color-border)] bg-white p-4 hover:shadow-md transition-shadow">
      <div className={`inline-flex h-9 w-9 items-center justify-center rounded-lg ${bg} mb-3`}>
        {icon}
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">{label}</p>
      {sub && <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">{sub}</p>}
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : <div>{inner}</div>;
}
