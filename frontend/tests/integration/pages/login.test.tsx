import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import LoginPage from "@/app/(auth)/login/page";
import { AuthProvider } from "@/lib/auth/context";
import * as session from "@/lib/auth/session";
import { mockHRUser, mockEmployeeUser } from "@/tests/mocks/data";

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

function renderLogin() {
  return render(
    <AuthProvider>
      <LoginPage />
    </AuthProvider>
  );
}

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue({
    replace: jest.fn(),
    push: jest.fn(),
  });
});

describe("LoginPage", () => {
  it("renders the sign-in heading", () => {
    renderLogin();
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
  });

  it("renders email and password fields", () => {
    renderLogin();
    expect(screen.getByPlaceholderText("hr@demo.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("demo1234")).toBeInTheDocument();
  });

  it("renders SkillsHub brand", () => {
    renderLogin();
    expect(screen.getAllByText("SkillsHub").length).toBeGreaterThan(0);
  });

  it("renders demo credentials panel", () => {
    renderLogin();
    expect(screen.getByText("Demo credentials")).toBeInTheDocument();
  });

  it("renders link to registration page", () => {
    renderLogin();
    expect(
      screen.getByRole("link", { name: /create an account/i })
    ).toBeInTheDocument();
  });

  it("submit button is labeled 'Sign in' by default", () => {
    renderLogin();
    expect(
      screen.getByRole("button", { name: /^sign in$/i })
    ).toBeInTheDocument();
  });

  it("shows loading text while submitting", async () => {
    // Delay api response so we can catch the loading state
    mockApi.mockReturnValueOnce(new Promise(() => {}));
    const user = userEvent.setup();
    renderLogin();

    await user.type(screen.getByPlaceholderText("hr@demo.com"), "hr@demo.com");
    await user.type(screen.getByPlaceholderText("demo1234"), "demo1234");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /^sign in$/i }).closest("form")!
      );
    });
    expect(screen.getByRole("button", { name: /signing in/i })).toBeInTheDocument();
  });

  it("redirects HR user to /dashboard after login", async () => {
    const mockReplace = jest.fn();
    (useRouter as jest.Mock).mockReturnValue({ replace: mockReplace });
    mockApi.mockResolvedValueOnce({
      access_token: "hr-tok",
      user: mockHRUser,
    });
    const user = userEvent.setup();
    renderLogin();

    await user.type(screen.getByPlaceholderText("hr@demo.com"), "hr@demo.com");
    await user.type(screen.getByPlaceholderText("demo1234"), "demo1234");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /^sign in$/i }).closest("form")!
      );
    });

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("redirects employee to /upload after login", async () => {
    const mockReplace = jest.fn();
    (useRouter as jest.Mock).mockReturnValue({ replace: mockReplace });
    mockApi.mockResolvedValueOnce({
      access_token: "emp-tok",
      user: mockEmployeeUser,
    });
    const user = userEvent.setup();
    renderLogin();

    await user.type(screen.getByPlaceholderText("hr@demo.com"), "emp@demo.com");
    await user.type(screen.getByPlaceholderText("demo1234"), "demo1234");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /^sign in$/i }).closest("form")!
      );
    });

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/upload");
    });
  });

  it("displays API error message for invalid credentials", async () => {
    mockApi.mockRejectedValueOnce(new ApiError(401, "Invalid credentials"));
    const user = userEvent.setup();
    renderLogin();

    await user.type(screen.getByPlaceholderText("hr@demo.com"), "bad@demo.com");
    await user.type(screen.getByPlaceholderText("demo1234"), "wrongpass");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /^sign in$/i }).closest("form")!
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });

  it("displays generic error on unexpected failure", async () => {
    mockApi.mockRejectedValueOnce(new Error("Network error"));
    const user = userEvent.setup();
    renderLogin();

    await user.type(screen.getByPlaceholderText("hr@demo.com"), "hr@demo.com");
    await user.type(screen.getByPlaceholderText("demo1234"), "demo1234");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /^sign in$/i }).closest("form")!
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/login failed/i)).toBeInTheDocument();
    });
  });

  it("saves session in localStorage on successful login", async () => {
    mockApi.mockResolvedValueOnce({
      access_token: "mock-hr-token",
      user: mockHRUser,
    });
    const user = userEvent.setup();
    renderLogin();

    await user.type(screen.getByPlaceholderText("hr@demo.com"), "hr@demo.com");
    await user.type(screen.getByPlaceholderText("demo1234"), "demo1234");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /^sign in$/i }).closest("form")!
      );
    });

    await waitFor(() => {
      expect(session.getToken()).toBe("mock-hr-token");
    });
  });
});
