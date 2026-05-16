import React from "react";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  useEmployees,
  useEmployee,
  useMyEmployee,
  useSearch,
  useReviewQueue,
  useReviewDetail,
  useApprove,
  useReject,
  useUploadResume,
  useUploadText,
  useTeamBuilder,
  useSkillGaps,
  useSkillsCatalog,
  useBulkUpload,
  useGitHubSync,
  useCreateEmployee,
} from "@/lib/api/hooks";
import {
  mockEmployeeListItem,
  mockPartialEmployee,
  mockAllocatedEmployee,
  mockEmployeeDetail,
  mockSearchResponse,
  mockReviewQueueItem,
  mockReviewDetail,
  mockUploadResponse,
  mockTeamBuilderResponse,
  mockSkillGapResponse,
  mockBulkUploadResponse,
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

import { api, ApiError } from "@/lib/api/client";
const mockApi = api as jest.Mock;

function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

// ─── useEmployees ────────────────────────────────────────────────────────────

describe("useEmployees", () => {
  it("fetches all employees successfully", async () => {
    mockApi.mockResolvedValueOnce([mockEmployeeListItem, mockPartialEmployee, mockAllocatedEmployee]);
    const { result } = renderHook(() => useEmployees(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(3);
  });

  it("calls API with encoded query param when filter supplied", async () => {
    mockApi.mockResolvedValueOnce([mockEmployeeListItem]);
    const { result } = renderHook(() => useEmployees("Jane"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApi).toHaveBeenCalledWith("/employees?q=Jane");
  });

  it("returns error state on API failure", async () => {
    mockApi.mockRejectedValueOnce(new ApiError(403, "Forbidden"));
    const { result } = renderHook(() => useEmployees(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

// ─── useEmployee ─────────────────────────────────────────────────────────────

describe("useEmployee", () => {
  it("fetches employee detail by id", async () => {
    mockApi.mockResolvedValueOnce(mockEmployeeDetail);
    const { result } = renderHook(() => useEmployee("emp-123"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.name).toBe("Jane Smith");
  });

  it("is disabled when id is null", () => {
    const { result } = renderHook(() => useEmployee(null), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe("idle");
    expect(result.current.data).toBeUndefined();
  });

  it("returns error for non-existent employee", async () => {
    mockApi.mockRejectedValueOnce(new ApiError(404, "Employee not found"));
    const { result } = renderHook(() => useEmployee("not-found"), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as { status?: number })?.status).toBe(404);
  });
});

// ─── useMyEmployee ────────────────────────────────────────────────────────────

describe("useMyEmployee", () => {
  it("fetches the current user's employee profile", async () => {
    mockApi.mockResolvedValueOnce(mockEmployeeDetail);
    const { result } = renderHook(() => useMyEmployee(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.email).toBe("jane@company.com");
  });

  it("does not retry on 404", async () => {
    mockApi.mockRejectedValueOnce(new ApiError(404, "Not found"));
    const { result } = renderHook(() => useMyEmployee(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.failureCount).toBe(1);
  });
});

// ─── useSearch ───────────────────────────────────────────────────────────────

describe("useSearch", () => {
  it("calls /search endpoint and returns results", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    const { result } = renderHook(() => useSearch(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate({ query: "React developer" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.results).toHaveLength(1);
    expect(result.current.data?.results[0].name).toBe("Jane Smith");
  });

  it("passes conversation history in the request body", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    const { result } = renderHook(() => useSearch(), { wrapper: createWrapper() });
    const history = [{ role: "user" as const, content: "prior query" }];

    await act(async () => {
      result.current.mutate({ query: "follow up", conversation_history: history });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const body = JSON.parse(mockApi.mock.calls[0][1].body);
    expect(body.conversation_history).toEqual(history);
  });

  it("returns error state on search failure", async () => {
    mockApi.mockRejectedValueOnce(new ApiError(500, "Server error"));
    const { result } = renderHook(() => useSearch(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate({ query: "failing query" });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

// ─── useReviewQueue ───────────────────────────────────────────────────────────

describe("useReviewQueue", () => {
  it("fetches review queue items", async () => {
    mockApi.mockResolvedValueOnce([mockReviewQueueItem]);
    const { result } = renderHook(() => useReviewQueue(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data![0].candidate_name).toBe("Jane Smith");
  });

  it("is defined (hook mounts without error)", () => {
    mockApi.mockResolvedValueOnce([]);
    const { result } = renderHook(() => useReviewQueue(), { wrapper: createWrapper() });
    expect(result.current).toBeDefined();
  });
});

// ─── useReviewDetail ──────────────────────────────────────────────────────────

describe("useReviewDetail", () => {
  it("fetches review detail by id", async () => {
    mockApi.mockResolvedValueOnce(mockReviewDetail);
    const { result } = renderHook(() => useReviewDetail("upload-1"), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.upload_id).toBe("upload-1");
  });

  it("is disabled when id is null", () => {
    const { result } = renderHook(() => useReviewDetail(null), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe("idle");
  });
});

// ─── useApprove ───────────────────────────────────────────────────────────────

describe("useApprove", () => {
  it("calls the approve endpoint with the upload id", async () => {
    mockApi.mockResolvedValueOnce({ message: "Approved" });
    const { result } = renderHook(() => useApprove(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate("upload-1");
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApi).toHaveBeenCalledWith(
      "/review-queue/upload-1/approve",
      expect.objectContaining({ method: "POST" })
    );
  });
});

// ─── useReject ────────────────────────────────────────────────────────────────

describe("useReject", () => {
  it("calls the reject endpoint with upload id and reason", async () => {
    mockApi.mockResolvedValueOnce({ message: "Rejected" });
    const { result } = renderHook(() => useReject(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate({ uploadId: "upload-1", reason: "Incomplete data" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockApi).toHaveBeenCalledWith(
      "/review-queue/upload-1/reject",
      expect.objectContaining({ method: "POST" })
    );
    const body = JSON.parse(mockApi.mock.calls[0][1].body);
    expect(body.reason).toBe("Incomplete data");
  });
});

// ─── useUploadResume ──────────────────────────────────────────────────────────

describe("useUploadResume", () => {
  it("uploads PDF and returns upload response", async () => {
    mockApi.mockResolvedValueOnce(mockUploadResponse);
    const { result } = renderHook(() => useUploadResume(), { wrapper: createWrapper() });
    const fd = new FormData();
    fd.append("file", new File(["content"], "resume.pdf", { type: "application/pdf" }));

    await act(async () => {
      result.current.mutate(fd);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.status).toBe("pending_review");
    expect(result.current.data?.upload_id).toBe("upload-abc123");
  });
});

// ─── useUploadText ────────────────────────────────────────────────────────────

describe("useUploadText", () => {
  it("uploads text and returns upload response", async () => {
    mockApi.mockResolvedValueOnce(mockUploadResponse);
    const { result } = renderHook(() => useUploadText(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate({ text: "Jane Smith - 5 years React" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.message).toBe("Resume submitted for review");
  });
});

// ─── useTeamBuilder ───────────────────────────────────────────────────────────

describe("useTeamBuilder", () => {
  it("builds a team proposal", async () => {
    mockApi.mockResolvedValueOnce(mockTeamBuilderResponse);
    const { result } = renderHook(() => useTeamBuilder(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate({
        description: "E-Commerce platform rebuild",
        team_size: 4,
        duration_weeks: 12,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.proposal.team).toHaveLength(1);
    expect(result.current.data?.proposal.team[0].name).toBe("Jane Smith");
  });
});

// ─── useSkillGaps ─────────────────────────────────────────────────────────────

describe("useSkillGaps", () => {
  it("fetches skill gap data", async () => {
    mockApi.mockResolvedValueOnce(mockSkillGapResponse);
    const { result } = renderHook(() => useSkillGaps(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total_employees).toBe(12);
    expect(result.current.data?.items).toHaveLength(3);
  });

  it("returns critical, warning, and healthy severity items", async () => {
    mockApi.mockResolvedValueOnce(mockSkillGapResponse);
    const { result } = renderHook(() => useSkillGaps(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const severities = result.current.data!.items.map((i) => i.gap_severity);
    expect(severities).toContain("critical");
    expect(severities).toContain("warning");
    expect(severities).toContain("healthy");
  });
});

// ─── useSkillsCatalog ─────────────────────────────────────────────────────────

describe("useSkillsCatalog", () => {
  it("fetches skills catalog", async () => {
    const catalog = [
      { id: "s-1", name: "React", category: "framework" },
      { id: "s-2", name: "TypeScript", category: "language" },
      { id: "s-3", name: "Node.js", category: "runtime" },
    ];
    mockApi.mockResolvedValueOnce(catalog);
    const { result } = renderHook(() => useSkillsCatalog(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(3);
    expect(result.current.data![0].name).toBe("React");
  });
});

// ─── useBulkUpload ────────────────────────────────────────────────────────────

describe("useBulkUpload", () => {
  it("uploads multiple resumes and returns bulk response", async () => {
    mockApi.mockResolvedValueOnce(mockBulkUploadResponse);
    const { result } = renderHook(() => useBulkUpload(), { wrapper: createWrapper() });
    const fd = new FormData();
    fd.append("files", new File(["content"], "r1.pdf"));
    fd.append("files", new File(["content"], "r2.pdf"));

    await act(async () => {
      result.current.mutate(fd);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total).toBe(2);
    expect(result.current.data?.queued).toBe(2);
    expect(result.current.data?.failed).toBe(0);
  });
});

// ─── useGitHubSync ────────────────────────────────────────────────────────────

describe("useGitHubSync", () => {
  it("syncs GitHub profile for an employee", async () => {
    mockApi.mockResolvedValueOnce(mockEmployeeDetail);
    const { result } = renderHook(() => useGitHubSync("emp-123"), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ github_username: "janesmith" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.name).toBe("Jane Smith");
    expect(mockApi).toHaveBeenCalledWith(
      "/employees/emp-123/github",
      expect.objectContaining({ method: "POST" })
    );
  });
});

// ─── useCreateEmployee ────────────────────────────────────────────────────────

describe("useCreateEmployee", () => {
  it("creates a new employee", async () => {
    mockApi.mockResolvedValueOnce(mockEmployeeDetail);
    const { result } = renderHook(() => useCreateEmployee(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate({
        name: "New Employee",
        email: "new@company.com",
        password: "pass123",
        title: "Junior Developer",
        location: "London",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeDefined();
    expect(mockApi).toHaveBeenCalledWith(
      "/employees",
      expect.objectContaining({ method: "POST" })
    );
  });
});
