import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6 py-24">
      <div className="max-w-2xl text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-muted)] px-3 py-1 text-xs text-[var(--color-muted-foreground)]">
          <span className="h-2 w-2 rounded-full bg-[var(--color-success)]" />
          AI-Powered Skills Intelligence
        </div>
        <h1 className="text-5xl font-semibold tracking-tight sm:text-6xl">
          SkillsHub
        </h1>
        <p className="mt-6 text-lg text-[var(--color-muted-foreground)]">
          Smart resume ingestion. Semantic HR search. Real reasoning behind every result.
        </p>
        <div className="mt-10 flex items-center justify-center gap-3">
          <Link
            href="/login"
            className="rounded-md bg-[var(--color-primary)] px-5 py-2.5 text-sm font-medium text-[var(--color-primary-foreground)] transition hover:opacity-90"
          >
            Sign in
          </Link>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
            target="_blank"
            rel="noreferrer"
            className="rounded-md border border-[var(--color-border)] px-5 py-2.5 text-sm font-medium transition hover:bg-[var(--color-muted)]"
          >
            API docs
          </a>
        </div>
      </div>
    </main>
  );
}
