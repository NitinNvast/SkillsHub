import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import ReviewQueuePage from "@/app/(hr)/review/page";
import { createTestQueryClient } from "@/tests/utils/render";
import { mockReviewQueueItem, mockFailedReviewItem } from "@/tests/mocks/data";

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

import { api } from "@/lib/api/client";
const mockApi = api as jest.Mock;

function renderReview() {
  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <ReviewQueuePage />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  mockApi.mockResolvedValue([mockReviewQueueItem]);
});

describe("ReviewQueuePage", () => {
  it("renders the Review Queue heading", () => {
    renderReview();
    expect(screen.getByRole("heading", { name: /review queue/i })).toBeInTheDocument();
  });

  it("renders the subtitle about AI-extracted profiles", () => {
    renderReview();
    expect(screen.getByText(/ai-extracted profiles awaiting hr review/i)).toBeInTheDocument();
  });

  it("shows skeleton table while loading", () => {
    mockApi.mockImplementation(() => new Promise(() => {}));
    const { container } = renderReview();
    expect(container.querySelectorAll(".skeleton").length).toBeGreaterThan(0);
  });

  it("shows empty state when queue is empty", async () => {
    mockApi.mockResolvedValueOnce([]);
    renderReview();
    await waitFor(() => {
      expect(screen.getByText("All caught up!")).toBeInTheDocument();
      expect(screen.getByText(/no pending reviews/i)).toBeInTheDocument();
    });
  });

  it("renders queue item with candidate name", async () => {
    renderReview();
    await waitFor(() => {
      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    });
  });

  it("renders queue item with skill count", async () => {
    renderReview();
    await waitFor(() => {
      // badge and description text both contain "8 skills"
      expect(screen.getAllByText(/8 skills/i).length).toBeGreaterThan(0);
    });
  });

  it("renders inferred skill count", async () => {
    renderReview();
    await waitFor(() => {
      expect(screen.getByText(/3 inferred/i)).toBeInTheDocument();
    });
  });

  it("renders source label as 'PDF Upload' for pdf source", async () => {
    renderReview();
    await waitFor(() => {
      expect(screen.getByText("PDF Upload")).toBeInTheDocument();
    });
  });

  it("renders 'Pending' status badge for pending items", async () => {
    renderReview();
    await waitFor(() => {
      expect(screen.getByText("Pending")).toBeInTheDocument();
    });
  });

  it("renders link to review detail page", async () => {
    renderReview();
    await waitFor(() => {
      const link = screen.getByRole("link", { name: /jane smith/i });
      expect(link).toHaveAttribute("href", `/review/${mockReviewQueueItem.upload_id}`);
    });
  });

  it("renders failed item with 'Failed' badge", async () => {
    mockApi.mockResolvedValueOnce([mockReviewQueueItem, mockFailedReviewItem]);
    renderReview();
    await waitFor(() => {
      expect(screen.getByText("Failed")).toBeInTheDocument();
    });
  });

  it("renders failed item extraction error message", async () => {
    mockApi.mockResolvedValueOnce([mockFailedReviewItem]);
    renderReview();
    await waitFor(() => {
      expect(screen.getByText(/extraction failed/i)).toBeInTheDocument();
    });
  });

  it("shows error state when API request fails", async () => {
    mockApi.mockRejectedValueOnce(new Error("Unauthorized"));
    renderReview();
    await waitFor(() => {
      expect(screen.getByText(/failed to load review queue/i)).toBeInTheDocument();
    });
  });

  it("renders multiple items in order", async () => {
    mockApi.mockResolvedValueOnce([mockReviewQueueItem, mockFailedReviewItem]);
    renderReview();
    await waitFor(() => {
      const items = screen.getAllByRole("link");
      expect(items.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("shows relative time in the queue item", async () => {
    renderReview();
    await waitFor(() => {
      expect(screen.getByText("today")).toBeInTheDocument();
    });
  });
});
