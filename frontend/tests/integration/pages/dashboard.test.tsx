import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import DashboardPage from "@/app/(hr)/dashboard/page";
import { createTestQueryClient } from "@/tests/utils/render";
import {
  mockEmployeeListItem,
  mockPartialEmployee,
  mockAllocatedEmployee,
  mockReviewQueueItem,
  mockSkillGapResponse,
} from "@/tests/mocks/data";

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

jest.mock("@/lib/auth/context", () => ({
  useAuth: () => ({
    user: { id: "hr-1", email: "hr@demo.com", name: "HR User", role: "hr" },
    loading: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import { api } from "@/lib/api/client";
const mockApi = api as jest.Mock;

const defaultEmployees = [mockEmployeeListItem, mockPartialEmployee, mockAllocatedEmployee];

function setupMocks({
  employees = defaultEmployees,
  queue = [mockReviewQueueItem],
  gaps = mockSkillGapResponse,
} = {}) {
  mockApi.mockImplementation((url: string) => {
    if (url.startsWith("/employees")) return Promise.resolve(employees);
    if (url === "/review-queue") return Promise.resolve(queue);
    if (url === "/skills/gaps") return Promise.resolve(gaps);
    return Promise.reject(new Error(`Unexpected API call: ${url}`));
  });
}

function renderDashboard() {
  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <DashboardPage />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  setupMocks();
});

describe("DashboardPage", () => {
  it("renders a greeting with the user's first name", async () => {
    renderDashboard();
    // greeting uses first name only: "Good morning/afternoon/evening, HR"
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/HR/);
    });
  });

  it("renders the overview subtitle", () => {
    renderDashboard();
    expect(screen.getByText(/overview of your talent pool/i)).toBeInTheDocument();
  });

  it("shows skeleton cards while loading", () => {
    mockApi.mockImplementation(() => new Promise(() => {}));
    const { container } = renderDashboard();
    expect(container.querySelectorAll(".skeleton").length).toBeGreaterThan(0);
  });

  it("shows Total Employees stat card", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Total Employees")).toBeInTheDocument();
    });
  });

  it("shows Available Now stat card", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Available Now")).toBeInTheDocument();
    });
  });

  it("shows Partially Free stat card", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Partially Free")).toBeInTheDocument();
    });
  });

  it("shows Pending Reviews stat card", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Pending Reviews")).toBeInTheDocument();
    });
  });

  it("shows correct total employee count", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument();
    });
  });

  it("renders Availability Breakdown section", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Availability Breakdown")).toBeInTheDocument();
    });
  });

  it("renders availability rows for all 3 statuses", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Available")).toBeInTheDocument();
      expect(screen.getByText("Partially available")).toBeInTheDocument();
      expect(screen.getByText("Fully allocated")).toBeInTheDocument();
    });
  });

  it("renders Pending Reviews section with queue items", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    });
  });

  it("renders Skill Gap Analysis when data available", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Skill Gap Analysis")).toBeInTheDocument();
    });
  });

  it("shows critical/warning/healthy counts in skill gap teaser", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Critical")).toBeInTheDocument();
      expect(screen.getByText("Low coverage")).toBeInTheDocument();
      expect(screen.getByText("Healthy")).toBeInTheDocument();
    });
  });

  it("renders quick action links to Search and Employee Directory", async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Talent Search")).toBeInTheDocument();
      expect(screen.getByText("Employee Directory")).toBeInTheDocument();
    });
  });

  it("shows 'All caught up!' when review queue is empty", async () => {
    setupMocks({ queue: [] });
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("All caught up!")).toBeInTheDocument();
    });
  });

  it("shows 'No employees yet.' when employee list is empty", async () => {
    setupMocks({ employees: [] });
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("No employees yet.")).toBeInTheDocument();
    });
  });

  it("shows percentage of team available", async () => {
    renderDashboard();
    await waitFor(() => {
      // 1 available out of 3 = 33%
      expect(screen.getByText(/33% of team/i)).toBeInTheDocument();
    });
  });
});
