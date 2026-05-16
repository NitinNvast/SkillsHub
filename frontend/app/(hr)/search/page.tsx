"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, RotateCcw, X } from "lucide-react";
import { toast } from "sonner";
import { useSearch, type SearchResponse, type ConversationMessage } from "@/lib/api/hooks";
import { ResultCard } from "@/components/search/ResultCard";

const DEMO_QUERIES = [
  "Who can lead a React project that also needs WebSocket experience?",
  "Full-stack developers with cloud (AWS or GCP) and microservices experience.",
  "Find a machine learning engineer with NLP and model deployment experience.",
  "Senior Java developer in Hyderabad with 5+ years of Spring Boot, available now.",
  "DevOps engineers with at least 4 years of Kubernetes and 2+ years of Terraform.",
  "React developers based in Bangalore who are currently unallocated.",
];

interface ChatTurn {
  query: string;
  response: SearchResponse | null;
  error: string | null;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const { mutate, isPending } = useSearch();
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, isPending]);

  function buildHistory(): ConversationMessage[] {
    const history: ConversationMessage[] = [];
    for (const turn of turns) {
      history.push({ role: "user", content: turn.query });
      if (turn.response) {
        const summary = `Found ${turn.response.total_candidates_retrieved} candidates. Top result: ${turn.response.results[0]?.name ?? "none"} (${turn.response.results[0]?.match_score ?? 0}% match). Interpreted as: ${turn.response.parsed_query.semantic_text}`;
        history.push({ role: "assistant", content: summary });
      }
    }
    return history;
  }

  function handleSearch(q: string) {
    if (!q.trim() || isPending) return;
    const trimmed = q.trim();
    setQuery("");
    mutate(
      { query: trimmed, conversation_history: buildHistory() },
      {
        onSuccess: (data) => {
          setTurns((prev) => [...prev, { query: trimmed, response: data, error: null }]);
        },
        onError: (err) => {
          const msg = err.message || "Search failed. Please try again.";
          toast.error(msg);
          setTurns((prev) => [...prev, { query: trimmed, response: null, error: msg }]);
        },
      }
    );
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch(query);
    }
  }

  function clearChat() {
    setTurns([]);
    setQuery("");
    inputRef.current?.focus();
  }

  const isEmpty = turns.length === 0 && !isPending;

  return (
    <div className="flex flex-col h-full max-h-screen">
      {/* Header */}
      <div className="px-4 sm:px-8 pt-8 pb-4 border-b border-[var(--color-border)] shrink-0">
        <div className="max-w-4xl mx-auto flex items-end justify-between gap-4">
          <div>
            <div className="w-8 h-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full mb-3" />
            <h1 className="text-2xl font-bold">Talent Search</h1>
            <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
              Ask in plain English — follow up to refine results.
            </p>
          </div>
          {turns.length > 0 && (
            <button
              onClick={clearChat}
              className="flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs font-medium text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] transition cursor-pointer"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              New search
            </button>
          )}
        </div>
      </div>

      {/* Chat body */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        <div className="max-w-4xl mx-auto space-y-8">

          {/* Empty state */}
          {isEmpty && (
            <div className="animate-fade-up flex flex-col items-center text-center py-8">
              {/* Hero icon */}
              <div className="mb-4 h-16 w-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                <Sparkles className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-xl font-bold mb-2">Ask in plain English</h2>
              <p className="text-sm text-[var(--color-muted-foreground)] max-w-md leading-relaxed mb-8">
                Describe who you&apos;re looking for — skills, years, location, availability — in natural language.
              </p>

              {/* Demo query chips */}
              <div className="flex flex-wrap justify-center gap-2 max-w-2xl">
                {DEMO_QUERIES.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSearch(q)}
                    className="rounded-full border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-2 text-xs text-[var(--color-muted-foreground)] hover:bg-[var(--color-primary)]/5 hover:border-[var(--color-primary)]/30 hover:text-[var(--color-foreground)] transition text-left cursor-pointer"
                  >
                    {q.length > 60 ? q.slice(0, 57) + "…" : q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Conversation turns */}
          {turns.map((turn, i) => (
            <div key={i} className="space-y-4 animate-fade-up">
              {/* User bubble */}
              <div className="flex justify-end">
                <div className="max-w-xl rounded-2xl rounded-tr-sm bg-gradient-to-br from-indigo-500 to-indigo-600 px-4 py-3 text-sm text-white shadow-sm">
                  {turn.query}
                </div>
              </div>

              {/* Error */}
              {turn.error && (
                <div className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
                  {turn.error}
                </div>
              )}

              {/* Results */}
              {turn.response && (
                <div className="space-y-4">
                  {/* Parsed query card */}
                  <div className="rounded-xl border border-[var(--color-border)] bg-gradient-to-r from-indigo-50/50 to-violet-50/50 dark:from-indigo-900/10 dark:to-violet-900/10 p-4 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="h-4 w-4 text-[var(--color-primary)]" />
                      <span className="text-xs font-semibold text-[var(--color-primary)]">AI Query Understanding</span>
                    </div>
                    <p className="text-sm text-[var(--color-foreground)]">{turn.response.parsed_query.semantic_text}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {turn.response.parsed_query.required_skills.map((s) => (
                        <span key={s} className="rounded-full bg-blue-50 border border-blue-200 px-2 py-0.5 text-xs text-blue-700">
                          Required: {s}
                        </span>
                      ))}
                      {Object.entries(turn.response.parsed_query.min_years_per_skill).map(([k, v]) => (
                        <span key={k} className="rounded-full bg-amber-50 border border-amber-200 px-2 py-0.5 text-xs text-amber-700">
                          {k} ≥ {v}y
                        </span>
                      ))}
                      {turn.response.parsed_query.location && (
                        <span className="rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-xs text-emerald-700">
                          📍 {turn.response.parsed_query.location}
                        </span>
                      )}
                      {turn.response.parsed_query.seniority_hint && (
                        <span className="rounded-full bg-purple-50 border border-purple-200 px-2 py-0.5 text-xs text-purple-700">
                          {turn.response.parsed_query.seniority_hint}
                        </span>
                      )}
                    </div>
                    <p className="mt-2 text-xs text-[var(--color-muted-foreground)]">
                      Retrieved {turn.response.total_candidates_retrieved} candidates · showing top {turn.response.results.length}
                    </p>
                  </div>

                  {turn.response.results.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-[var(--color-border)] p-8 text-center">
                      <p className="text-sm text-[var(--color-muted-foreground)]">No matching candidates found.</p>
                      <p className="text-xs text-[var(--color-muted-foreground)] mt-1">Try broadening your query.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {turn.response.results.map((r, j) => (
                        <ResultCard key={r.employee_id} result={r} rank={j + 1} />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Pending indicator */}
          {isPending && (
            <div className="space-y-4 animate-fade-up">
              <div className="flex justify-end">
                <div className="max-w-xl rounded-2xl rounded-tr-sm bg-gradient-to-br from-indigo-500 to-indigo-600 px-4 py-3 text-sm text-white shadow-sm opacity-70">
                  {query || "…"}
                </div>
              </div>
              <div className="flex flex-col items-start gap-3 py-4">
                <div className="flex items-center gap-3">
                  <div className="relative h-8 w-8">
                    <div className="absolute inset-0 rounded-full border-3 border-indigo-100" />
                    <div className="absolute inset-0 rounded-full border-3 border-transparent border-t-indigo-500 animate-spin" />
                  </div>
                  <p className="text-sm text-[var(--color-muted-foreground)]">Parsing query → searching → ranking with AI…</p>
                </div>
                {[...Array(2)].map((_, i) => (
                  <div key={i} className="skeleton h-36 rounded-xl w-full" style={{ animationDelay: `${i * 100}ms` }} />
                ))}
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input bar */}
      <div className="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-background)] px-4 sm:px-8 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="relative rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] shadow-sm focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/25 focus-within:shadow-lg transition-all duration-150">
            <textarea
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={turns.length > 0 ? "Follow up or refine…" : "Who can lead a React project with WebSocket experience?"}
              rows={2}
              className="w-full resize-none rounded-xl bg-transparent px-5 py-4 pr-28 text-sm outline-none placeholder:text-[var(--color-muted-foreground)]"
            />
            <div className="absolute right-3 bottom-3 flex gap-2">
              {query && (
                <button
                  onClick={() => setQuery("")}
                  className="rounded-lg p-1.5 text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] transition cursor-pointer"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={() => handleSearch(query)}
                disabled={isPending || !query.trim()}
                className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50 hover:from-indigo-600 hover:to-indigo-700 transition cursor-pointer"
              >
                {isPending ? (
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
                Send
              </button>
            </div>
          </div>
          {turns.length > 0 && (
            <p className="mt-2 text-xs text-[var(--color-muted-foreground)] text-center">
              Conversation context is passed with each query — ask follow-up questions to refine
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
