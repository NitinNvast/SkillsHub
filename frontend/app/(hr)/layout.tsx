"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { LayoutDashboard, Search, ClipboardList, Users, LogOut } from "lucide-react";
import { useAuth } from "@/lib/auth/context";
import { useReviewQueue } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard",  label: "Dashboard",    icon: LayoutDashboard },
  { href: "/search",     label: "Search",        icon: Search },
  { href: "/review",     label: "Review Queue",  icon: ClipboardList, badge: true },
  { href: "/employees",  label: "Directory",     icon: Users },
];

export default function HRLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const { data: queue } = useReviewQueue();
  const pendingCount = queue?.length ?? 0;

  useEffect(() => {
    if (!loading && (!user || user.role !== "hr")) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <div className="flex h-screen bg-[var(--color-muted)]">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 flex flex-col bg-white border-r border-[var(--color-border)]">
        <div className="px-5 py-5 border-b border-[var(--color-border)]">
          <p className="font-semibold text-base">SkillsHub</p>
          <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">HR Portal</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV.map(({ href, label, icon: Icon, badge }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-[var(--color-primary)] text-white"
                    : "text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] hover:text-[var(--color-foreground)]",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
                {badge && pendingCount > 0 && (
                  <span className={cn(
                    "ml-auto rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                    active ? "bg-white/20 text-white" : "bg-red-100 text-red-700"
                  )}>
                    {pendingCount}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="px-3 pb-4 border-t border-[var(--color-border)] pt-3">
          <div className="flex items-center gap-2 px-3 py-2 mb-1">
            <div className="h-7 w-7 rounded-full bg-[var(--color-primary)] flex items-center justify-center text-white text-xs font-bold">
              {user.name[0]}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium truncate">{user.name}</p>
              <p className="text-[10px] text-[var(--color-muted-foreground)] truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] hover:text-[var(--color-foreground)] transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
