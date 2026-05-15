"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Upload, User, LogOut, Brain, Menu, X } from "lucide-react";
import { useAuth } from "@/lib/auth/context";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/upload",  label: "Upload Resume", icon: Upload },
  { href: "/profile", label: "My Profile",    icon: User   },
];

function SidebarContent({
  user, pathname, logout, onNavClick,
}: {
  user: { name: string; email: string };
  pathname: string;
  logout: () => void;
  onNavClick?: () => void;
}) {
  return (
    <>
      <div className="px-5 py-5 border-b border-[var(--color-sidebar-border)]">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shrink-0">
            <Brain className="h-4 w-4 text-white" />
          </div>
          <span className="font-bold text-base bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
            SkillsHub
          </span>
        </div>
        <p className="text-xs text-[var(--color-sidebar-foreground)] mt-1.5 opacity-50 ml-0.5">My Portal</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
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
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-4 border-t border-[var(--color-sidebar-border)] pt-3 space-y-0.5">
        <div className="flex items-center gap-2.5 px-3 py-2 mb-1">
          <div className="h-8 w-8 rounded-full ring-2 ring-purple-400/40 bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
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

export default function EmployeeLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!loading && (!user || user.role !== "employee")) router.replace("/login");
  }, [user, loading, router]);

  useEffect(() => { setMobileOpen(false); }, [pathname]);

  if (loading || !user) return null;

  return (
    <div className="flex h-screen bg-[var(--color-background)]">
      <aside className="hidden md:flex w-60 shrink-0 flex-col bg-[var(--color-sidebar)] border-r border-[var(--color-sidebar-border)]">
        <SidebarContent user={user} pathname={pathname} logout={logout} />
      </aside>

      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden animate-fade-in"
          onClick={() => setMobileOpen(false)}
        />
      )}

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
          logout={logout}
          onNavClick={() => setMobileOpen(false)}
        />
      </aside>

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-[var(--color-sidebar)] border-b border-[var(--color-sidebar-border)] shrink-0">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
              <Brain className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="font-bold text-sm bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
              SkillsHub
            </span>
          </div>
          <button
            onClick={() => setMobileOpen(true)}
            className="p-1.5 rounded-lg text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)] transition-colors"
          >
            <Menu className="h-5 w-5" />
          </button>
        </header>
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
