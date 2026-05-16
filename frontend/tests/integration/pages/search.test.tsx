import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import SearchPage from "@/app/(hr)/search/page";
import { createTestQueryClient } from "@/tests/utils/render";
import { toast } from "sonner";
import { mockSearchResponse, mockEmptySearchResponse } from "@/tests/mocks/data";

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

function renderSearch() {
  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <SearchPage />
    </QueryClientProvider>
  );
}

describe("SearchPage", () => {
  it("renders the Talent Search heading", () => {
    renderSearch();
    expect(
      screen.getByRole("heading", { name: /talent search/i })
    ).toBeInTheDocument();
  });

  it("renders empty state with demo query chips", () => {
    renderSearch();
    expect(screen.getAllByText(/ask in plain english/i).length).toBeGreaterThan(0);
    // demo query chips are buttons
    expect(screen.getAllByRole("button").length).toBeGreaterThan(1);
  });

  it("renders placeholder text in textarea", () => {
    renderSearch();
    expect(
      screen.getByPlaceholderText(/who can lead a react project/i)
    ).toBeInTheDocument();
  });

  it("Send button is disabled when textarea is empty", () => {
    renderSearch();
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("Send button enables after typing in textarea", async () => {
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "Find React developers");
    expect(screen.getByRole("button", { name: /send/i })).not.toBeDisabled();
  });

  it("submits query on Send button click and shows results", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "React developer");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await waitFor(() =>
      expect(screen.getByText("Jane Smith")).toBeInTheDocument()
    );
  });

  it("submits query on Enter key (without Shift)", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    const user = userEvent.setup();
    renderSearch();
    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "React developer");
    await act(async () => {
      fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });
    });
    await waitFor(() =>
      expect(screen.getByText("Jane Smith")).toBeInTheDocument()
    );
  });

  it("does NOT submit on Shift+Enter", async () => {
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "query");
    fireEvent.keyDown(screen.getByRole("textbox"), {
      key: "Enter",
      shiftKey: true,
    });
    expect(mockApi).not.toHaveBeenCalled();
  });

  it("shows AI Query Understanding card after search", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "React developer");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await waitFor(() =>
      expect(screen.getByText("AI Query Understanding")).toBeInTheDocument()
    );
  });

  it("shows parsed semantic text", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "React developer");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await waitFor(() =>
      expect(
        screen.getByText(mockSearchResponse.parsed_query.semantic_text)
      ).toBeInTheDocument()
    );
  });

  it("shows required skill chips from parsed query", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "React developer");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await waitFor(() =>
      expect(screen.getByText("Required: React")).toBeInTheDocument()
    );
  });

  it("shows 'No matching candidates found' for empty results", async () => {
    mockApi.mockResolvedValueOnce(mockEmptySearchResponse);
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "quantum computing");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await waitFor(() =>
      expect(
        screen.getByText(/no matching candidates found/i)
      ).toBeInTheDocument()
    );
  });

  it("shows error toast on search failure", async () => {
    const { ApiError } = jest.requireActual("@/lib/api/client");
    mockApi.mockRejectedValueOnce(new ApiError(500, "Search failed"));
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "failing query");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await waitFor(() => expect(toast.error).toHaveBeenCalled());
  });

  it("shows 'New search' button after first query", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "React developer");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /new search/i })
      ).toBeInTheDocument()
    );
  });

  it("clicking 'New search' clears conversation history", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    const user = userEvent.setup();
    renderSearch();
    await user.type(screen.getByRole("textbox"), "React developer");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await waitFor(() => screen.getByRole("button", { name: /new search/i }));
    await user.click(screen.getByRole("button", { name: /new search/i }));
    expect(screen.queryByText("Jane Smith")).not.toBeInTheDocument();
    expect(screen.getAllByText(/ask in plain english/i).length).toBeGreaterThan(0);
  });

  it("clicking a demo query chip triggers a search", async () => {
    mockApi.mockResolvedValueOnce(mockSearchResponse);
    renderSearch();
    const chips = screen.getAllByRole("button");
    // First button is a demo query chip (Send is disabled and not first)
    const chip = chips.find((b) => b.textContent && b.textContent.length > 10);
    await act(async () => {
      fireEvent.click(chip!);
    });
    await waitFor(() =>
      expect(screen.getByText("Jane Smith")).toBeInTheDocument()
    );
  });

  it("passes conversation history on follow-up query", async () => {
    mockApi.mockResolvedValue(mockSearchResponse);
    const user = userEvent.setup();
    renderSearch();

    // First query
    await user.type(screen.getByRole("textbox"), "React developers");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });
    await waitFor(() => screen.getByText("Jane Smith"));

    // Second query (follow-up)
    await user.type(screen.getByRole("textbox"), "in Bangalore only");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /send/i }));
    });

    await waitFor(() => {
      const secondCall = mockApi.mock.calls[1];
      const body = JSON.parse(secondCall[1].body);
      expect(body.conversation_history).toHaveLength(2);
    });
  });
});
