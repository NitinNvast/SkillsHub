"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Brain, Zap, Search, Shield } from "lucide-react";
import { useAuth } from "@/lib/auth/context";
import { ApiError } from "@/lib/api/client";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

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
    <div className="h-screen overflow-hidden flex">
      {/* Left panel — brand + features */}
      <div className="hidden lg:flex lg:w-1/2 flex-col items-center justify-center relative bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700 p-12 overflow-hidden">
        {/* Subtle mesh grid overlay */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.25) 1px, transparent 0)",
            backgroundSize: "24px 24px",
          }}
        />

        {/* Content */}
        <div className="relative z-10 text-center max-w-sm">
          <div className="inline-flex items-center justify-center gap-3 mb-5">
            <Brain className="h-12 w-12 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">SkillsHub</h1>
          <p className="text-lg text-white/80 mb-10">AI-Powered Skills Intelligence</p>

          <div className="space-y-4 text-left">
            {[
              { icon: <Zap className="h-5 w-5 text-white/90" />, label: "AI extracts skills from any resume in seconds" },
              { icon: <Search className="h-5 w-5 text-white/90" />, label: "Search your talent pool in plain English" },
              { icon: <Shield className="h-5 w-5 text-white/90" />, label: "HR review gate ensures data quality" },
            ].map(({ icon, label }) => (
              <div key={label} className="flex items-center gap-3 text-white/80">
                <div className="shrink-0 h-9 w-9 rounded-lg bg-white/15 flex items-center justify-center">
                  {icon}
                </div>
                <span className="text-sm leading-snug">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex flex-col items-center justify-center bg-[var(--color-background)] px-6 relative">
        {/* Theme toggle top-right */}
        <div className="absolute top-4 right-4">
          <ThemeToggle variant="floating" />
        </div>

        <div className="w-full max-w-sm animate-fade-up">
          {/* Mobile-only branding */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center justify-center gap-2 mb-2">
              <Brain className="h-7 w-7 text-indigo-600" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                SkillsHub
              </h1>
            </div>
            <p className="text-sm text-[var(--color-muted-foreground)]">AI-Powered Skills Intelligence</p>
          </div>

          <div className="rounded-xl border border-[var(--color-border)] border-t-4 border-t-indigo-500 bg-[var(--color-card)] p-8 shadow-xl">
            <h2 className="text-lg font-semibold mb-6">Sign in</h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="hr@demo.com"
                  required
                  className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
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
                  className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
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
                className="w-full rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-600 py-2.5 text-sm font-semibold text-white hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-60 transition cursor-pointer"
              >
                {loading ? "Signing in…" : "Sign in"}
              </button>
            </form>

            <div className="mt-6 rounded-lg bg-[var(--color-muted)] p-3 text-xs text-[var(--color-muted-foreground)] space-y-1">
              <p className="font-semibold text-[var(--color-foreground)]">Demo credentials</p>
              <p>HR: <span className="font-mono">hr@demo.com</span> / <span className="font-mono">demo1234</span></p>
              <p>Employee: <span className="font-mono">emp@demo.com</span> / <span className="font-mono">demo1234</span></p>
            </div>

            <p className="mt-5 text-center text-xs text-[var(--color-muted-foreground)]">
              New employee?{" "}
              <Link href="/register" className="text-indigo-600 hover:underline font-medium">
                Create an account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
