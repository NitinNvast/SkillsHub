/**
 * JWT session helpers — stores token + user in localStorage.
 * Server components read from cookies; this is the client-side counterpart.
 */

export interface SessionUser {
  id: string;
  email: string;
  name: string;
  role: "hr" | "employee";
}

const TOKEN_KEY = "skillshub_jwt";
const USER_KEY  = "skillshub_user";

export function saveSession(token: string, user: SessionUser): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): SessionUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}
