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
  className?: string;
}

export function SkillChip({ name, category = "tool", proficiency, years, inferred, className }: Props) {
  const style = CATEGORY_STYLES[category] ?? CATEGORY_STYLES.tool;
  const dot   = proficiency ? PROFICIENCY_DOT[proficiency] : null;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold",
        style,
        className,
      )}
      title={[proficiency, years ? `${years}y` : null, inferred ? "inferred" : null].filter(Boolean).join(" · ")}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", dot)} />}
      {inferred && <span className="opacity-70 text-[11px]">✨</span>}
      {name}
      {years != null && <span className="opacity-50 text-[10px] font-medium">{years}y</span>}
    </span>
  );
}
