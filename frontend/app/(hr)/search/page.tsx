"use client";

import { useState, useRef } from "react";
import { Search, Sparkles, X } from "lucide-react";
import { useSearch } from "@/lib/api/hooks";
import { ResultCard } from "@/components/search/ResultCard";

const DEMO_QUERIES = [
  "Who can lead a React project that also needs WebSocket experience?",
  "Find a backend dev in Pune with at least 3 years of Java and payment gateway integration.",
  "Senior frontend engineers who haven't been on a new project recently.",
  "Full-stack developers with cloud (AWS or GCP) and microservices experience.",
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const { mutate, data, isPending, error, reset } = useSearch();
  const inputRef = useRef<HTMLTextAreaElement>(null);

  function handleSearch(q: string) {
    if (!q.trim()) return;
    mutate({ query: q.trim() });
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch(query);
    }
  }

  return (
    <div className="px-8 py-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">Talent Search</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          Ask in plain English — get ranked candidates with AI reasoning.
        </p>
      </div>

      {/* Search box */}
      <div className="relative rounded-xl border-2 border-[var(--color-primary)] bg-white shadow-sm focus-within:shadow-md transition-shadow">
        <textarea
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Who can lead a React project with WebSocket experience?"
          rows={2}
          className="w-full resize-none rounded-xl bg-transparent px-5 py-4 text-sm outline-none placeholder:text-[var(--color-muted-foreground)]"
        />
        <div className="absolute right-3 bottom-3 flex gap-2">
          {query && (
            <button
              onClick={() => { setQuery(""); reset(); inputRef.current?.focus(); }}
              className="rounded-lg p-1.5 text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] transition"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={() => handleSearch(query)}
            disabled={isPending || !query.trim()}
            className="flex items-center gap-1.5 rounded-lg bg-[var(--color-primary)] px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50 hover:opacity-90 transition"
          >
            {isPending ? (
              <span className="flex items-center gap-1.5">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Searching…
              </span>
            ) : (
              <><Search className="h-3.5 w-3.5" /> Search</>
            )}
          </button>
        </div>
      </div>

      {/* Demo query chips */}
      {!data && !isPending && (
        <div className="mt-4">
          <p className="text-xs text-[var(--color-muted-foreground)] mb-2">Try these queries:</p>
          <div className="flex flex-wrap gap-2">
            {DEMO_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => { setQuery(q); handleSearch(q); }}
                className="rounded-full border border-[var(--color-border)] bg-white px-3 py-1.5 text-xs text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] hover:text-[var(--color-foreground)] transition text-left"
              >
                {q.length > 60 ? q.slice(0, 57) + "…" : q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading state */}
      {isPending && (
        <div className="mt-10 text-center space-y-3">
          <div className="flex justify-center">
            <Sparkles className="h-8 w-8 text-[var(--color-primary)] animate-pulse" />
          </div>
          <p className="text-sm text-[var(--color-muted-foreground)]">Parsing query → searching → ranking with AI…</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-6 rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
          {error.message}
        </div>
      )}

      {/* Results */}
      {data && !isPending && (
        <div className="mt-8 space-y-6">
          {/* Parsed query display */}
          <div className="rounded-xl border border-[var(--color-border)] bg-white p-4">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-4 w-4 text-[var(--color-primary)]" />
              <span className="text-xs font-medium text-[var(--color-primary)]">AI Query Understanding</span>
            </div>
            <p className="text-sm text-[var(--color-foreground)]">{data.parsed_query.semantic_text}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {data.parsed_query.required_skills.map((s) => (
                <span key={s} className="rounded-full bg-blue-50 border border-blue-200 px-2 py-0.5 text-xs text-blue-700">
                  Required: {s}
                </span>
              ))}
              {Object.entries(data.parsed_query.min_years_per_skill).map(([k, v]) => (
                <span key={k} className="rounded-full bg-amber-50 border border-amber-200 px-2 py-0.5 text-xs text-amber-700">
                  {k} ≥ {v}y
                </span>
              ))}
              {data.parsed_query.location && (
                <span className="rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-xs text-emerald-700">
                  📍 {data.parsed_query.location}
                </span>
              )}
              {data.parsed_query.seniority_hint && (
                <span className="rounded-full bg-purple-50 border border-purple-200 px-2 py-0.5 text-xs text-purple-700">
                  {data.parsed_query.seniority_hint}
                </span>
              )}
            </div>
            <p className="mt-2 text-xs text-[var(--color-muted-foreground)]">
              Retrieved {data.total_candidates_retrieved} candidates · showing top {data.results.length}
            </p>
          </div>

          {data.results.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[var(--color-border)] p-10 text-center">
              <p className="text-sm text-[var(--color-muted-foreground)]">No matching candidates found.</p>
              <p className="text-xs text-[var(--color-muted-foreground)] mt-1">Try broadening your query or uploading more resumes.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {data.results.map((r, i) => (
                <ResultCard key={r.employee_id} result={r} rank={i + 1} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
