/**
 * Thin fetch wrapper that:
 *  - prefixes NEXT_PUBLIC_API_URL
 *  - attaches the JWT from localStorage (set on login)
 *  - throws on non-2xx with a parsed error
 *
 * Server-side usage (RSC/Server Actions) should read the JWT from cookies instead.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message);
  }
}

export async function api<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const jwt = token ?? (typeof window !== "undefined" ? localStorage.getItem("skillshub_jwt") : null);
  if (jwt) headers.set("Authorization", `Bearer ${jwt}`);

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    throw new ApiError(res.status, data?.detail ?? res.statusText, data);
  }
  return data as T;
}
