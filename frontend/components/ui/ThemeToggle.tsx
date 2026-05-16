"use client";

import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/lib/theme/context";
import { cn } from "@/lib/utils";

interface Props {
  className?: string;
  /** "sidebar" renders with sidebar text colours; "floating" renders as a floating pill */
  variant?: "sidebar" | "floating" | "inline";
}

export function ThemeToggle({ className, variant = "sidebar" }: Props) {
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  if (variant === "floating") {
    return (
      <button
        onClick={toggleTheme}
        title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        className={cn(
          "fixed top-4 right-4 z-50 flex items-center gap-2 rounded-full border px-3 py-1.5",
          "bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm",
          "border-slate-200 dark:border-slate-700",
          "text-xs font-medium text-slate-700 dark:text-slate-200",
          "shadow-md hover:shadow-lg transition-all cursor-pointer",
          className,
        )}
      >
        {isDark
          ? <Sun key="sun-float" className="theme-icon-enter h-3.5 w-3.5 text-amber-500" />
          : <Moon key="moon-float" className="theme-icon-enter h-3.5 w-3.5 text-indigo-500" />}
        {isDark ? "Light" : "Dark"}
      </button>
    );
  }

  if (variant === "inline") {
    return (
      <button
        onClick={toggleTheme}
        title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        className={cn(
          "flex items-center justify-center h-8 w-8 rounded-lg",
          "bg-[var(--color-muted)] hover:bg-[var(--color-border)]",
          "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]",
          "transition-colors cursor-pointer",
          className,
        )}
      >
        {isDark
          ? <Sun key="sun-inline" className="theme-icon-enter h-4 w-4 text-amber-500" />
          : <Moon key="moon-inline" className="theme-icon-enter h-4 w-4 text-indigo-500" />}
      </button>
    );
  }

  // sidebar variant — styled for dark sidebar
  return (
    <button
      onClick={toggleTheme}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className={cn(
        "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm",
        "text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)]",
        "transition-colors cursor-pointer",
        className,
      )}
    >
      {isDark
        ? <Sun key="sun-sidebar" className="theme-icon-enter h-4 w-4 text-amber-400 shrink-0" />
        : <Moon key="moon-sidebar" className="theme-icon-enter h-4 w-4 text-indigo-500 shrink-0" />}
      {isDark ? "Light mode" : "Dark mode"}
    </button>
  );
}
