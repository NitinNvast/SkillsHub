import React from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { SessionUser } from "@/lib/auth/session";

// Re-export everything from RTL for convenience
export * from "@testing-library/react";

// ─── QueryClient factory ────────────────────────────────────────────────────

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// ─── Custom render with React Query ─────────────────────────────────────────

interface RenderWithQueryOptions extends RenderOptions {
  queryClient?: QueryClient;
}

export function renderWithQuery(
  ui: React.ReactElement,
  { queryClient, ...options }: RenderWithQueryOptions = {}
) {
  const client = queryClient ?? createTestQueryClient();
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  }
  return { ...render(ui, { wrapper: Wrapper, ...options }), queryClient: client };
}

// ─── Mock auth context ───────────────────────────────────────────────────────

export interface MockAuthState {
  user?: SessionUser | null;
  loading?: boolean;
  login?: jest.Mock;
  register?: jest.Mock;
  logout?: jest.Mock;
}

export function buildMockAuth(overrides: MockAuthState = {}) {
  return {
    user: overrides.user !== undefined ? overrides.user : null,
    loading: overrides.loading ?? false,
    login: overrides.login ?? jest.fn(),
    register: overrides.register ?? jest.fn(),
    logout: overrides.logout ?? jest.fn(),
  };
}

// ─── Combined render with Query + mocked Auth ────────────────────────────────

interface RenderWithProvidersOptions extends RenderWithQueryOptions {
  authState?: MockAuthState;
}

export function renderWithProviders(
  ui: React.ReactElement,
  { authState, queryClient, ...options }: RenderWithProvidersOptions = {}
) {
  const mockAuth = buildMockAuth(authState);

  // Patch useAuth at module level before rendering
  jest.mock("@/lib/auth/context", () => ({
    useAuth: () => mockAuth,
    AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  }));

  return renderWithQuery(ui, { queryClient, ...options });
}
