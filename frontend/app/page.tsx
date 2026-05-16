import Link from "next/link";
import { Brain, Zap, Search, Shield } from "lucide-react";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6 py-24 bg-gradient-to-br from-slate-50 via-indigo-50 to-slate-100 dark:from-slate-900 dark:via-indigo-950 dark:to-slate-900">
      <ThemeToggle variant="floating" />
      <div className="max-w-2xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-slate-200 dark:border-white/10 bg-slate-100 dark:bg-white/5 px-3 py-1 text-xs text-slate-500 dark:text-slate-300 backdrop-blur-sm">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          AI-Powered Skills Intelligence
        </div>

        <div className="flex items-center justify-center gap-3 mb-4">
          <Brain className="h-10 w-10 text-blue-500 dark:text-blue-400" />
          <h1 className="text-5xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-6xl">
            SkillsHub
          </h1>
        </div>

        <p className="mt-4 text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
          Smart resume ingestion. Semantic HR search. Real reasoning behind every result.
        </p>

        {/* Feature highlights */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4 text-sm text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-blue-500 dark:text-blue-400 shrink-0" />
            <span>AI extracts skills from any resume</span>
          </div>
          <div className="hidden sm:block h-4 w-px bg-slate-300 dark:bg-slate-700" />
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-purple-500 dark:text-purple-400 shrink-0" />
            <span>Ask in plain English to find talent</span>
          </div>
          <div className="hidden sm:block h-4 w-px bg-slate-300 dark:bg-slate-700" />
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-emerald-500 dark:text-emerald-400 shrink-0" />
            <span>HR review gate before publishing</span>
          </div>
        </div>

        <div className="mt-10 flex items-center justify-center gap-3">
          <Link
            href="/login"
            className="rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:from-indigo-600 hover:to-indigo-700 cursor-pointer"
          >
            Sign in
          </Link>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-slate-200 dark:border-white/20 bg-slate-100 dark:bg-white/10 px-6 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-200 backdrop-blur-sm transition hover:bg-slate-200 dark:hover:bg-white/20 cursor-pointer"
          >
            API docs
          </a>
        </div>
      </div>
    </main>
  );
}
