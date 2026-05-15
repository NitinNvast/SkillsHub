"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AuthProvider } from "@/lib/auth/context";
import { ThemeProvider } from "@/lib/theme/context";
import { Toaster } from "sonner";

export function Providers({ children }: { children: React.ReactNode }) {
  const [qc] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { retry: 1, refetchOnWindowFocus: false },
    },
  }));

  return (
    <ThemeProvider>
      <QueryClientProvider client={qc}>
        <AuthProvider>
          {children}
          <Toaster
            position="bottom-right"
            toastOptions={{
              classNames: {
                toast: "font-sans text-sm",
                success: "border-l-4 border-emerald-500",
                error: "border-l-4 border-red-500",
              },
            }}
            richColors
            closeButton
          />
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
