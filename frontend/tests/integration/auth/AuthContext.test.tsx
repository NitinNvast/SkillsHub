import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/lib/auth/context";
import * as session from "@/lib/auth/session";
import { mockHRUser, mockEmployeeUser } from "@/tests/mocks/data";

// Mock the api module — no MSW needed
jest.mock("@/lib/api/client", () => {
  class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
      public detail?: unknown
    ) {
      super(message);
    }
  }
  return { api: jest.fn(), ApiError };
});

import { api, ApiError } from "@/lib/api/client";
const mockApi = api as jest.Mock;

function TestConsumer() {
  const { user, loading, login, register, logout } = useAuth();
  if (loading) return <div>Loading…</div>;
  if (!user)
    return (
      <div>
        <span>No user</span>
        <button onClick={() => login("hr@demo.com", "demo1234").catch(() => {})}>Login HR</button>
        <button onClick={() => login("emp@demo.com", "demo1234").catch(() => {})}>Login Emp</button>
        <button onClick={() => register("New User", "new@demo.com", "pass123").catch(() => {})}>
          Register
        </button>
      </div>
    );
  return (
    <div>
      <span>User: {user.name}</span>
      <span>Role: {user.role}</span>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

function renderAuth() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>
  );
}

beforeEach(() => {
  window.location.href = "";
});

describe("AuthProvider", () => {
  it("shows loading initially then resolves", async () => {
    renderAuth();
    await waitFor(() =>
      expect(screen.queryByText("Loading…")).not.toBeInTheDocument()
    );
  });

  it("reads user from localStorage on mount", async () => {
    session.saveSession("existing-token", mockHRUser);
    renderAuth();
    await waitFor(() =>
      expect(screen.getByText("User: HR User")).toBeInTheDocument()
    );
  });

  it("shows no user when localStorage is empty", async () => {
    renderAuth();
    await waitFor(() =>
      expect(screen.getByText("No user")).toBeInTheDocument()
    );
  });

  it("login calls api and stores session", async () => {
    mockApi.mockResolvedValueOnce({
      access_token: "mock-hr-token",
      user: mockHRUser,
    });
    renderAuth();
    await waitFor(() => screen.getByText("No user"));

    await act(async () => {
      screen.getByText("Login HR").click();
    });

    await waitFor(() => {
      expect(screen.getByText("User: HR User")).toBeInTheDocument();
      expect(session.getToken()).toBe("mock-hr-token");
    });
  });

  it("login calls /auth/login endpoint", async () => {
    mockApi.mockResolvedValueOnce({
      access_token: "tok",
      user: mockHRUser,
    });
    renderAuth();
    await waitFor(() => screen.getByText("No user"));
    await act(async () => {
      screen.getByText("Login HR").click();
    });
    await waitFor(() => screen.getByText("User: HR User"));
    expect(mockApi).toHaveBeenCalledWith(
      "/auth/login",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("login stores employee role correctly", async () => {
    mockApi.mockResolvedValueOnce({
      access_token: "emp-token",
      user: mockEmployeeUser,
    });
    renderAuth();
    await waitFor(() => screen.getByText("No user"));
    await act(async () => {
      screen.getByText("Login Emp").click();
    });
    await waitFor(() =>
      expect(screen.getByText("Role: employee")).toBeInTheDocument()
    );
  });

  it("login propagates ApiError without storing session", async () => {
    mockApi.mockRejectedValueOnce(new ApiError(401, "Invalid credentials"));
    renderAuth();
    await waitFor(() => screen.getByText("No user"));

    await act(async () => {
      screen.getByText("Login HR").click();
    });

    // Session should NOT be saved on error
    await new Promise((r) => setTimeout(r, 50));
    expect(session.getToken()).toBeNull();
  });

  it("register calls api and stores session", async () => {
    const newUser = {
      id: "new-1",
      email: "new@demo.com",
      name: "New User",
      role: "employee" as const,
    };
    mockApi.mockResolvedValueOnce({
      access_token: "mock-new-token",
      user: newUser,
    });
    renderAuth();
    await waitFor(() => screen.getByText("No user"));
    await act(async () => {
      screen.getByText("Register").click();
    });
    await waitFor(() => {
      expect(screen.getByText("User: New User")).toBeInTheDocument();
      expect(session.getToken()).toBe("mock-new-token");
    });
  });

  it("logout clears session and redirects to /login", async () => {
    session.saveSession("token", mockHRUser);
    renderAuth();
    await waitFor(() => screen.getByText("User: HR User"));

    screen.getByText("Logout").click();

    await waitFor(() => {
      expect(session.getToken()).toBeNull();
      expect(window.location.href).toBe("/login");
    });
  });
});
