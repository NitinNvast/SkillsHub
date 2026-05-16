import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import RegisterPage from "@/app/(auth)/register/page";
import { AuthProvider } from "@/lib/auth/context";
import * as session from "@/lib/auth/session";

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

function renderRegister() {
  return render(
    <AuthProvider>
      <RegisterPage />
    </AuthProvider>
  );
}

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue({ replace: jest.fn(), push: jest.fn() });
});

describe("RegisterPage", () => {
  it("renders the create account heading", () => {
    renderRegister();
    expect(
      screen.getByRole("heading", { name: /create your account/i })
    ).toBeInTheDocument();
  });

  it("renders all four input fields", () => {
    renderRegister();
    expect(screen.getByPlaceholderText("Jane Smith")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("jane@company.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/min. 6 characters/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/re-enter password/i)).toBeInTheDocument();
  });

  it("renders link to login page", () => {
    renderRegister();
    expect(screen.getByRole("link", { name: /sign in/i })).toHaveAttribute(
      "href",
      "/login"
    );
  });

  it("shows password mismatch error without calling api", async () => {
    const mockReplace = jest.fn();
    (useRouter as jest.Mock).mockReturnValue({ replace: mockReplace });
    const user = userEvent.setup();
    renderRegister();

    await user.type(screen.getByPlaceholderText("Jane Smith"), "Test User");
    await user.type(screen.getByPlaceholderText("jane@company.com"), "test@example.com");
    await user.type(screen.getByPlaceholderText(/min. 6 characters/i), "password123");
    await user.type(screen.getByPlaceholderText(/re-enter password/i), "different456");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /create account/i }).closest("form")!
      );
    });

    expect(screen.getByText("Passwords do not match.")).toBeInTheDocument();
    expect(mockReplace).not.toHaveBeenCalled();
    expect(mockApi).not.toHaveBeenCalled();
  });

  it("redirects to /upload after successful registration", async () => {
    const mockReplace = jest.fn();
    (useRouter as jest.Mock).mockReturnValue({ replace: mockReplace });
    mockApi.mockResolvedValueOnce({
      access_token: "new-token",
      user: { id: "1", email: "newuser@demo.com", name: "New User", role: "employee" },
    });
    const user = userEvent.setup();
    renderRegister();

    await user.type(screen.getByPlaceholderText("Jane Smith"), "New User");
    await user.type(screen.getByPlaceholderText("jane@company.com"), "newuser@demo.com");
    await user.type(screen.getByPlaceholderText(/min. 6 characters/i), "pass123");
    await user.type(screen.getByPlaceholderText(/re-enter password/i), "pass123");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /create account/i }).closest("form")!
      );
    });

    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith("/upload"));
  });

  it("trims whitespace from name before submitting", async () => {
    mockApi.mockResolvedValueOnce({
      access_token: "tok",
      user: { id: "1", email: "t@t.com", name: "Spaced Name", role: "employee" },
    });
    const user = userEvent.setup();
    renderRegister();

    await user.type(screen.getByPlaceholderText("Jane Smith"), "  Spaced Name  ");
    await user.type(screen.getByPlaceholderText("jane@company.com"), "t@t.com");
    await user.type(screen.getByPlaceholderText(/min. 6 characters/i), "pass123");
    await user.type(screen.getByPlaceholderText(/re-enter password/i), "pass123");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /create account/i }).closest("form")!
      );
    });

    await waitFor(() => {
      const body = JSON.parse(mockApi.mock.calls[0][1].body);
      expect(body.name).toBe("Spaced Name");
    });
  });

  it("shows API error message when registration fails", async () => {
    mockApi.mockRejectedValueOnce(new ApiError(400, "Email already registered"));
    const user = userEvent.setup();
    renderRegister();

    await user.type(screen.getByPlaceholderText("Jane Smith"), "Existing");
    await user.type(screen.getByPlaceholderText("jane@company.com"), "existing@demo.com");
    await user.type(screen.getByPlaceholderText(/min. 6 characters/i), "pass123");
    await user.type(screen.getByPlaceholderText(/re-enter password/i), "pass123");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /create account/i }).closest("form")!
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Email already registered")).toBeInTheDocument();
    });
  });

  it("shows loading text while submitting", async () => {
    mockApi.mockReturnValueOnce(new Promise(() => {}));
    const user = userEvent.setup();
    renderRegister();

    await user.type(screen.getByPlaceholderText("Jane Smith"), "Test");
    await user.type(screen.getByPlaceholderText("jane@company.com"), "t@t.com");
    await user.type(screen.getByPlaceholderText(/min. 6 characters/i), "pass123");
    await user.type(screen.getByPlaceholderText(/re-enter password/i), "pass123");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /create account/i }).closest("form")!
      );
    });

    expect(
      screen.getByRole("button", { name: /creating account/i })
    ).toBeInTheDocument();
  });

  it("stores session after successful registration", async () => {
    mockApi.mockResolvedValueOnce({
      access_token: "mock-new-token",
      user: { id: "1", email: "np@demo.com", name: "New Person", role: "employee" },
    });
    const user = userEvent.setup();
    renderRegister();

    await user.type(screen.getByPlaceholderText("Jane Smith"), "New Person");
    await user.type(screen.getByPlaceholderText("jane@company.com"), "np@demo.com");
    await user.type(screen.getByPlaceholderText(/min. 6 characters/i), "pass123");
    await user.type(screen.getByPlaceholderText(/re-enter password/i), "pass123");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /create account/i }).closest("form")!
      );
    });

    await waitFor(() => expect(session.getToken()).toBe("mock-new-token"));
  });
});
