"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/context";
import { ApiError } from "@/lib/api/client";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(email, password);
      router.replace(user.role === "hr" ? "/dashboard" : "/upload");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-muted)] px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold">SkillsHub</h1>
          <p className="text-sm text-[var(--color-muted-foreground)] mt-1">AI-Powered Skills Intelligence</p>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-white p-8 shadow-sm">
          <h2 className="text-lg font-medium mb-6">Sign in</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="hr@demo.com"
                required
                className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="demo1234"
                required
                className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition"
              />
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-[var(--color-primary)] py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60 transition"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="mt-6 rounded-lg bg-[var(--color-muted)] p-3 text-xs text-[var(--color-muted-foreground)] space-y-1">
            <p className="font-medium text-[var(--color-foreground)]">Demo credentials</p>
            <p>HR: <span className="font-mono">hr@demo.com</span> / <span className="font-mono">demo1234</span></p>
            <p>Employee: <span className="font-mono">emp@demo.com</span> / <span className="font-mono">demo1234</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}
