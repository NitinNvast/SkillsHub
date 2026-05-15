"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LayoutDashboard, Search, ClipboardList, Users, LogOut, Brain, Menu, X } from "lucide-react";
import { useAuth } from "@/lib/auth/context";
import { useReviewQueue } from "@/lib/api/hooks";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard",  label: "Dashboard",   icon: LayoutDashboard },
  { href: "/search",     label: "Search",       icon: Search },
  { href: "/review",     label: "Review Queue", icon: ClipboardList, badge: true },
  { href: "/employees",  label: "Directory",    icon: Users },
];

function SidebarContent({
  user, pathname, pendingCount, logout, onNavClick,
}: {
  user: { name: string; email: string };
  pathname: string;
  pendingCount: number;
  logout: () => void;
  onNavClick?: () => void;
}) {
  return (
    <>
      <div className="px-5 py-5 border-b border-[var(--color-sidebar-border)]">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shrink-0">
            <Brain className="h-4 w-4 text-white" />
          </div>
          <span className="font-bold text-base bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            SkillsHub
          </span>
        </div>
        <p className="text-xs text-[var(--color-sidebar-foreground)] mt-1.5 opacity-50 ml-0.5">HR Portal</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavClick}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                active
                  ? "bg-[var(--color-primary)] text-white shadow-sm"
                  : "text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)]",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
              {badge && pendingCount > 0 && (
                <span className={cn(
                  "ml-auto rounded-full px-1.5 py-0.5 text-[10px] font-bold",
                  active ? "bg-white/20 text-white" : "bg-red-500 text-white",
                )}>
                  {pendingCount}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-4 border-t border-[var(--color-sidebar-border)] pt-3 space-y-0.5">
        <div className="flex items-center gap-2.5 px-3 py-2 mb-1">
          <div className="h-8 w-8 rounded-full ring-2 ring-blue-400/40 bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
            {user.name[0]}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold truncate text-[var(--color-sidebar-foreground)]">{user.name}</p>
            <p className="text-[10px] text-[var(--color-sidebar-foreground)] opacity-50 truncate">{user.email}</p>
          </div>
        </div>
        <ThemeToggle />
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)] transition-colors cursor-pointer"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </>
  );
}

export default function HRLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const { data: queue } = useReviewQueue();
  const pendingCount = queue?.length ?? 0;
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!loading && (!user || user.role !== "hr")) router.replace("/login");
  }, [user, loading, router]);

  // Close mobile sidebar on route change
  useEffect(() => { setMobileOpen(false); }, [pathname]);

  if (loading || !user) return null;

  return (
    <div className="flex h-screen bg-[var(--color-background)]">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-60 shrink-0 flex-col bg-[var(--color-sidebar)] border-r border-[var(--color-sidebar-border)]">
        <SidebarContent user={user} pathname={pathname} pendingCount={pendingCount} logout={logout} />
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden animate-fade-in"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar drawer */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 flex flex-col bg-[var(--color-sidebar)] border-r border-[var(--color-sidebar-border)]",
        "md:hidden transition-transform duration-300 ease-in-out",
        mobileOpen ? "translate-x-0" : "-translate-x-full",
      )}>
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)] transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
        <SidebarContent
          user={user}
          pathname={pathname}
          pendingCount={pendingCount}
          logout={logout}
          onNavClick={() => setMobileOpen(false)}
        />
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile top bar */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-[var(--color-sidebar)] border-b border-[var(--color-sidebar-border)] shrink-0">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Brain className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="font-bold text-sm bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              SkillsHub
            </span>
          </div>
          <div className="flex items-center gap-2">
            {pendingCount > 0 && (
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                {pendingCount}
              </span>
            )}
            <button
              onClick={() => setMobileOpen(true)}
              className="p-1.5 rounded-lg text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)] transition-colors"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
