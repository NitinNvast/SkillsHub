"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, CheckCircle, Search, TrendingDown, Users, ChevronRight } from "lucide-react";
import { useSkillGaps, type SkillGapItem } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

type Severity = "all" | "critical" | "warning" | "healthy";
type Category = "all" | string;

const SEVERITY_CONFIG = {
  critical: {
    label: "Critical",
    description: "No employees have this skill",
    bar: "bg-red-500",
    badge: "bg-red-50 text-red-700 border-red-200",
    border: "border-l-red-500",
    dot: "bg-red-500",
    icon: "text-red-500",
  },
  warning: {
    label: "Low coverage",
    description: "Fewer than 25% of team",
    bar: "bg-amber-400",
    badge: "bg-amber-50 text-amber-700 border-amber-200",
    border: "border-l-amber-400",
    dot: "bg-amber-400",
    icon: "text-amber-500",
  },
  healthy: {
    label: "Healthy",
    description: "Good coverage across team",
    bar: "bg-emerald-500",
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
    border: "border-l-emerald-500",
    dot: "bg-emerald-500",
    icon: "text-emerald-500",
  },
};

const CATEGORY_LABELS: Record<string, string> = {
  language: "Languages",
  framework: "Frameworks",
  platform: "Platforms",
  tool: "Tools",
  domain: "Domain",
};

function CoverageBar({ pct, severity }: { pct: number; severity: "critical" | "warning" | "healthy" }) {
  const cfg = SEVERITY_CONFIG[severity];
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-[var(--color-muted)] overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-700", cfg.bar)}
          style={{ width: `${Math.max(pct, pct === 0 ? 0 : 2)}%` }}
        />
      </div>
      <span className="text-xs tabular-nums text-[var(--color-muted-foreground)] w-9 text-right">
        {pct === 0 ? "0%" : `${pct}%`}
      </span>
    </div>
  );
}

function SkillRow({
  item,
  totalEmployees,
  onSearch,
}: {
  item: SkillGapItem;
  totalEmployees: number;
  onSearch: (skill: string) => void;
}) {
  const cfg = SEVERITY_CONFIG[item.gap_severity];
  const novice = item.employee_count - item.expert_count - item.intermediate_count;

  return (
    <div
      className={cn(
        "group flex items-center gap-4 rounded-xl border border-[var(--color-border)] border-l-4 bg-[var(--color-card)] px-4 py-3 shadow-sm hover:shadow-md transition-all duration-150",
        cfg.border,
      )}
    >
      {/* Skill name + category */}
      <div className="min-w-0 w-40 shrink-0">
        <p className="text-sm font-semibold truncate">{item.name}</p>
        <p className="text-[10px] text-[var(--color-muted-foreground)] mt-0.5 capitalize">
          {CATEGORY_LABELS[item.category] ?? item.category}
        </p>
      </div>

      {/* Coverage bar */}
      <div className="flex-1 min-w-0">
        <CoverageBar pct={item.coverage_pct} severity={item.gap_severity} />
        <div className="flex items-center gap-3 mt-1.5">
          {item.employee_count === 0 ? (
            <span className="text-xs text-red-600 font-medium">Nobody on your team has this skill</span>
          ) : (
            <>
              <span className="text-xs text-[var(--color-muted-foreground)]">
                {item.employee_count}/{totalEmployees} people
              </span>
              {item.expert_count > 0 && (
                <span className="text-xs text-indigo-600 font-medium">{item.expert_count} expert</span>
              )}
              {item.intermediate_count > 0 && (
                <span className="text-xs text-[var(--color-muted-foreground)]">{item.intermediate_count} mid</span>
              )}
              {novice > 0 && (
                <span className="text-xs text-[var(--color-muted-foreground)]">{novice} novice</span>
              )}
            </>
          )}
        </div>
      </div>

      {/* Severity badge */}
      <span
        className={cn(
          "shrink-0 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold",
          cfg.badge,
        )}
      >
        {cfg.label}
      </span>

      {/* Find candidates */}
      <button
        onClick={() => onSearch(item.name)}
        className="shrink-0 flex items-center gap-1 text-xs text-[var(--color-muted-foreground)] opacity-0 group-hover:opacity-100 hover:text-[var(--color-primary)] transition-all cursor-pointer"
      >
        <Search className="h-3 w-3" />
        Find
        <ChevronRight className="h-3 w-3" />
      </button>
    </div>
  );
}

export default function SkillGapsPage() {
  const { data, isLoading } = useSkillGaps();
  const router = useRouter();
  const [severityFilter, setSeverityFilter] = useState<Severity>("all");
  const [categoryFilter, setCategoryFilter] = useState<Category>("all");
  const [search, setSearch] = useState("");

  const totalEmployees = data?.total_employees ?? 0;
  const allItems = data?.items ?? [];

  const critical = allItems.filter((i) => i.gap_severity === "critical");
  const warning = allItems.filter((i) => i.gap_severity === "warning");
  const healthy = allItems.filter((i) => i.gap_severity === "healthy");

  const categories = useMemo(() => {
    const cats = [...new Set(allItems.map((i) => i.category))].sort();
    return cats;
  }, [allItems]);

  const filtered = useMemo(() => {
    return allItems.filter((item) => {
      if (severityFilter !== "all" && item.gap_severity !== severityFilter) return false;
      if (categoryFilter !== "all" && item.category !== categoryFilter) return false;
      if (search && !item.name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [allItems, severityFilter, categoryFilter, search]);

  function handleFindCandidates(skill: string) {
    router.push(`/search?q=${encodeURIComponent(`engineers with ${skill} experience`)}`);
  }

  return (
    <div className="px-4 sm:px-8 py-8 max-w-5xl mx-auto animate-fade-up">
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-[var(--color-border)]">
        <div className="w-8 h-0.5 bg-gradient-to-r from-amber-400 to-orange-500 rounded-full mb-3" />
        <h1 className="text-2xl font-bold">Skill Gap Analysis</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          Skills your team is light on — ranked by how critical the gap is.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="skeleton h-16 rounded-xl" style={{ animationDelay: `${i * 50}ms` }} />
          ))}
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            <SummaryCard
              label="Total skills tracked"
              value={allItems.length}
              icon={<TrendingDown className="h-5 w-5 text-indigo-500" />}
              bg="bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-900/30 dark:to-indigo-800/20"
              active={severityFilter === "all"}
              onClick={() => setSeverityFilter("all")}
            />
            <SummaryCard
              label="Critical gaps"
              value={critical.length}
              icon={<AlertTriangle className="h-5 w-5 text-red-500" />}
              bg="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/20"
              active={severityFilter === "critical"}
              onClick={() => setSeverityFilter(severityFilter === "critical" ? "all" : "critical")}
              accent="border-l-red-500"
            />
            <SummaryCard
              label="Low coverage"
              value={warning.length}
              icon={<AlertTriangle className="h-5 w-5 text-amber-500" />}
              bg="bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-900/30 dark:to-amber-800/20"
              active={severityFilter === "warning"}
              onClick={() => setSeverityFilter(severityFilter === "warning" ? "all" : "warning")}
              accent="border-l-amber-400"
            />
            <SummaryCard
              label="Well covered"
              value={healthy.length}
              icon={<CheckCircle className="h-5 w-5 text-emerald-500" />}
              bg="bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900/30 dark:to-emerald-800/20"
              active={severityFilter === "healthy"}
              onClick={() => setSeverityFilter(severityFilter === "healthy" ? "all" : "healthy")}
              accent="border-l-emerald-500"
            />
          </div>

          {/* What do these mean */}
          <div className="mb-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 shadow-sm">
            <p className="text-xs font-semibold mb-2 text-[var(--color-foreground)]">How to read this</p>
            <div className="flex flex-wrap gap-4 text-xs text-[var(--color-muted-foreground)]">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-red-500 shrink-0" />
                <strong className="text-[var(--color-foreground)]">Critical</strong> — Nobody has this skill. You'd need to hire or train before taking on related projects.
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-400 shrink-0" />
                <strong className="text-[var(--color-foreground)]">Low coverage</strong> — Less than 25% of your team. Risk if those few people leave or are unavailable.
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500 shrink-0" />
                <strong className="text-[var(--color-foreground)]">Healthy</strong> — Good distribution. You can staff projects confidently.
              </span>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3 mb-5">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[var(--color-muted-foreground)]" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Filter skills…"
                className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] pl-8 pr-3 py-1.5 text-xs outline-none focus:ring-2 focus:ring-indigo-500/25 focus:border-indigo-500 transition w-44"
              />
            </div>

            {/* Category chips */}
            <div className="flex flex-wrap gap-1.5">
              {["all", ...categories].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs font-medium transition cursor-pointer",
                    categoryFilter === cat
                      ? "border-indigo-500 bg-indigo-500 text-white"
                      : "border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]",
                  )}
                >
                  {cat === "all" ? "All categories" : (CATEGORY_LABELS[cat] ?? cat)}
                </button>
              ))}
            </div>
          </div>

          {/* Team size context */}
          <div className="flex items-center gap-2 mb-4 text-xs text-[var(--color-muted-foreground)]">
            <Users className="h-3.5 w-3.5" />
            Showing coverage across {totalEmployees} employee{totalEmployees !== 1 ? "s" : ""} ·{" "}
            <span className="font-medium text-[var(--color-foreground)]">{filtered.length}</span> skills shown
          </div>

          {/* Skill list */}
          {filtered.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
              <p className="text-sm text-[var(--color-muted-foreground)]">No skills match your filters.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Critical group */}
              {severityFilter === "all" && critical.filter((i) => filtered.includes(i)).length > 0 && (
                <GapGroup
                  title="Critical — no coverage"
                  items={critical.filter((i) => filtered.includes(i))}
                  totalEmployees={totalEmployees}
                  onSearch={handleFindCandidates}
                />
              )}
              {/* Warning group */}
              {severityFilter === "all" && warning.filter((i) => filtered.includes(i)).length > 0 && (
                <GapGroup
                  title="Low coverage — under 25%"
                  items={warning.filter((i) => filtered.includes(i))}
                  totalEmployees={totalEmployees}
                  onSearch={handleFindCandidates}
                />
              )}
              {/* Healthy group */}
              {severityFilter === "all" && healthy.filter((i) => filtered.includes(i)).length > 0 && (
                <GapGroup
                  title="Healthy coverage"
                  items={healthy.filter((i) => filtered.includes(i))}
                  totalEmployees={totalEmployees}
                  onSearch={handleFindCandidates}
                />
              )}
              {/* Filtered single list */}
              {severityFilter !== "all" &&
                filtered.map((item) => (
                  <SkillRow
                    key={item.name}
                    item={item}
                    totalEmployees={totalEmployees}
                    onSearch={handleFindCandidates}
                  />
                ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function GapGroup({
  title,
  items,
  totalEmployees,
  onSearch,
}: {
  title: string;
  items: SkillGapItem[];
  totalEmployees: number;
  onSearch: (skill: string) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="mb-4">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 text-xs font-semibold text-[var(--color-muted-foreground)] uppercase tracking-wide mb-2 hover:text-[var(--color-foreground)] transition cursor-pointer"
      >
        <ChevronRight className={cn("h-3.5 w-3.5 transition-transform", !collapsed && "rotate-90")} />
        {title}
        <span className="ml-1 rounded-full bg-[var(--color-muted)] px-1.5 py-0.5 text-[10px] normal-case font-medium">
          {items.length}
        </span>
      </button>
      {!collapsed && (
        <div className="space-y-2">
          {items.map((item) => (
            <SkillRow
              key={item.name}
              item={item}
              totalEmployees={totalEmployees}
              onSearch={onSearch}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon,
  bg,
  active,
  onClick,
  accent,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  bg: string;
  active: boolean;
  onClick: () => void;
  accent?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-xl border border-[var(--color-border)] border-l-4 bg-[var(--color-card)] p-4 text-left shadow-sm transition-all duration-150 cursor-pointer w-full",
        active ? "ring-2 ring-indigo-500/30 shadow-md" : "hover:shadow-md",
        accent ?? "border-l-indigo-500",
      )}
    >
      <div className={cn("inline-flex h-9 w-9 items-center justify-center rounded-lg mb-2", bg)}>
        {icon}
      </div>
      <p className="text-xl font-bold tabular-nums">{value}</p>
      <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">{label}</p>
    </button>
  );
}
