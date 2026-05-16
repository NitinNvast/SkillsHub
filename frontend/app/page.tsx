import Link from "next/link";
import { Brain, Zap, Search, Shield } from "lucide-react";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

const FEATURES = [
  {
    icon: <Zap className="h-5 w-5 text-blue-500 dark:text-blue-400" />,
    title: "Instant Extraction",
    description: "AI extracts skills, projects, and certifications from any resume in seconds.",
  },
  {
    icon: <Search className="h-5 w-5 text-purple-500 dark:text-purple-400" />,
    title: "Plain English Search",
    description: "Ask in natural language to find talent. No filters, no query syntax.",
  },
  {
    icon: <Shield className="h-5 w-5 text-emerald-500 dark:text-emerald-400" />,
    title: "HR Review Gate",
    description: "Every profile passes through human review before going live.",
  },
];

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6 py-24 bg-gradient-to-br from-slate-50 via-indigo-50 to-slate-100 dark:from-slate-900 dark:via-indigo-950 dark:to-slate-900">
      <ThemeToggle variant="floating" />

      <div className="relative max-w-2xl text-center animate-fade-up">
        {/* Gradient orb behind title */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 -z-10 blur-3xl opacity-30 w-96 h-96 rounded-full bg-gradient-to-r from-indigo-400 to-purple-400 pointer-events-none" />

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

        {/* Feature cards — 3 column grid */}
        <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
          {FEATURES.map(({ icon, title, description }) => (
            <div
              key={title}
              className="rounded-xl border border-slate-200 dark:border-white/10 bg-white/70 dark:bg-white/5 backdrop-blur-sm p-4 hover:shadow-md transition-shadow duration-200"
            >
              <div className="mb-2">{icon}</div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-1">{title}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{description}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 flex items-center justify-center gap-3">
          <Link
            href="/login"
            className="rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:from-indigo-600 hover:to-indigo-700 cursor-pointer"
          >
            Sign in
          </Link>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-slate-200 dark:border-white/20 bg-slate-100 dark:bg-white/10 px-6 py-3 text-sm font-medium text-slate-700 dark:text-slate-200 backdrop-blur-sm transition hover:bg-slate-200 dark:hover:bg-white/20 cursor-pointer"
          >
            API docs
          </a>
        </div>
      </div>
    </main>
  );
}
