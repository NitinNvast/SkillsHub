import { cn } from "@/lib/utils";

const CATEGORY_STYLES: Record<string, string> = {
  language:  "bg-blue-50 text-blue-700 border-blue-200",
  framework: "bg-violet-50 text-violet-700 border-violet-200",
  platform:  "bg-orange-50 text-orange-700 border-orange-200",
  tool:      "bg-slate-50 text-slate-700 border-slate-200",
  domain:    "bg-emerald-50 text-emerald-700 border-emerald-200",
};

const PROFICIENCY_DOT: Record<string, string> = {
  expert:       "bg-emerald-500",
  intermediate: "bg-amber-400",
  novice:       "bg-slate-300",
};

interface Props {
  name: string;
  category?: string;
  proficiency?: string;
  years?: number | null;
  inferred?: boolean;
  fromGithub?: boolean;
  className?: string;
}

export function SkillChip({ name, category = "tool", proficiency, years, inferred, fromGithub, className }: Props) {
  const style = CATEGORY_STYLES[category] ?? CATEGORY_STYLES.tool;
  const dot   = proficiency ? PROFICIENCY_DOT[proficiency] : null;

  const titleParts = [
    proficiency,
    years ? `${years}y` : null,
    inferred ? "inferred" : null,
    fromGithub ? "from GitHub" : null,
  ].filter(Boolean).join(" · ");

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold",
        style,
        className,
      )}
      title={titleParts}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", dot)} />}
      {inferred && <span className="opacity-70 text-[11px]">✨</span>}
      {fromGithub && (
        <svg className="h-3 w-3 opacity-60 shrink-0" viewBox="0 0 16 16" fill="currentColor" aria-hidden>
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
        </svg>
      )}
      {name}
      {years != null && <span className="opacity-50 text-[10px] font-medium">{years}y</span>}
    </span>
  );
}
