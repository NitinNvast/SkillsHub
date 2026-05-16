import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import UploadPage from "@/app/(employee)/upload/page";
import { createTestQueryClient } from "@/tests/utils/render";
import { toast } from "sonner";
import { mockUploadResponse } from "@/tests/mocks/data";

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

function renderUpload() {
  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <UploadPage />
    </QueryClientProvider>
  );
}

describe("UploadPage", () => {
  it("renders the Upload Resume heading", () => {
    renderUpload();
    expect(
      screen.getByRole("heading", { name: /upload resume/i })
    ).toBeInTheDocument();
  });

  it("shows PDF and text tabs", () => {
    renderUpload();
    expect(screen.getByText("PDF Resume")).toBeInTheDocument();
    expect(screen.getByText("Paste Text")).toBeInTheDocument();
  });

  it("shows drop zone on PDF tab by default", () => {
    renderUpload();
    expect(screen.getByText(/drop your pdf here/i)).toBeInTheDocument();
  });

  it("switches to text tab on click", async () => {
    const user = userEvent.setup();
    renderUpload();
    await user.click(screen.getByText("Paste Text"));
    expect(
      screen.getByPlaceholderText(/paste your resume/i)
    ).toBeInTheDocument();
  });

  it("submit button disabled when textarea is empty", async () => {
    const user = userEvent.setup();
    renderUpload();
    await user.click(screen.getByText("Paste Text"));
    expect(
      screen.getByRole("button", { name: /extract skills with ai/i })
    ).toBeDisabled();
  });

  it("submit button enables after typing text", async () => {
    const user = userEvent.setup();
    renderUpload();
    await user.click(screen.getByText("Paste Text"));
    await user.type(
      screen.getByPlaceholderText(/paste your resume/i),
      "Jane Smith - Engineer"
    );
    expect(
      screen.getByRole("button", { name: /extract skills with ai/i })
    ).not.toBeDisabled();
  });

  it("shows success state after text upload", async () => {
    mockApi.mockResolvedValueOnce(mockUploadResponse);
    const user = userEvent.setup();
    renderUpload();
    await user.click(screen.getByText("Paste Text"));
    await user.type(
      screen.getByPlaceholderText(/paste your resume/i),
      "Jane Smith - 5 years React"
    );
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /extract skills with ai/i }).closest("form")!
      );
    });
    await waitFor(() =>
      expect(screen.getByText("Resume submitted!")).toBeInTheDocument()
    );
  });

  it("shows upload_id in success state", async () => {
    mockApi.mockResolvedValueOnce(mockUploadResponse);
    const user = userEvent.setup();
    renderUpload();
    await user.click(screen.getByText("Paste Text"));
    await user.type(screen.getByPlaceholderText(/paste your resume/i), "resume");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /extract skills with ai/i }).closest("form")!
      );
    });
    await waitFor(() =>
      expect(
        screen.getByText(mockUploadResponse.upload_id.slice(0, 8) + "…")
      ).toBeInTheDocument()
    );
  });

  it("shows Pending review status after upload", async () => {
    mockApi.mockResolvedValueOnce(mockUploadResponse);
    const user = userEvent.setup();
    renderUpload();
    await user.click(screen.getByText("Paste Text"));
    await user.type(screen.getByPlaceholderText(/paste your resume/i), "resume text");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /extract skills with ai/i }).closest("form")!
      );
    });
    await waitFor(() =>
      expect(screen.getByText("Pending review")).toBeInTheDocument()
    );
  });

  it("clicking 'Upload another resume' resets form", async () => {
    mockApi.mockResolvedValueOnce(mockUploadResponse);
    const user = userEvent.setup();
    renderUpload();
    await user.click(screen.getByText("Paste Text"));
    await user.type(screen.getByPlaceholderText(/paste your resume/i), "text");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /extract skills with ai/i }).closest("form")!
      );
    });
    await waitFor(() => screen.getByText("Upload another resume"));
    await user.click(screen.getByText("Upload another resume"));
    expect(
      screen.getByRole("heading", { name: /upload resume/i })
    ).toBeInTheDocument();
  });

  it("shows error panel when upload fails", async () => {
    const { ApiError } = jest.requireActual("@/lib/api/client");
    mockApi.mockRejectedValueOnce(new ApiError(500, "Server error"));
    const user = userEvent.setup();
    renderUpload();
    await user.click(screen.getByText("Paste Text"));
    await user.type(screen.getByPlaceholderText(/paste your resume/i), "bad text");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /extract skills with ai/i }).closest("form")!
      );
    });
    await waitFor(() =>
      expect(screen.getByText("Server error")).toBeInTheDocument()
    );
  });

  it("fires toast.success on successful upload", async () => {
    mockApi.mockResolvedValueOnce(mockUploadResponse);
    const user = userEvent.setup();
    renderUpload();
    await user.click(screen.getByText("Paste Text"));
    await user.type(screen.getByPlaceholderText(/paste your resume/i), "Jane Smith");
    await act(async () => {
      fireEvent.submit(
        screen.getByRole("button", { name: /extract skills with ai/i }).closest("form")!
      );
    });
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        "Resume submitted! AI is extracting your skills."
      );
    });
  });

  it("renders 'What happens after upload?' steps", () => {
    renderUpload();
    expect(screen.getByText("What happens after upload?")).toBeInTheDocument();
    expect(screen.getByText(/claude ai extracts skills/i)).toBeInTheDocument();
  });

  it("handles PDF file input change", async () => {
    mockApi.mockResolvedValueOnce(mockUploadResponse);
    renderUpload();
    const file = new File(["pdf content"], "resume.pdf", {
      type: "application/pdf",
    });
    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });
    await waitFor(() =>
      expect(screen.getByText("Resume submitted!")).toBeInTheDocument()
    );
  });

  it("ignores non-PDF files", async () => {
    renderUpload();
    const file = new File(["doc content"], "resume.docx", {
      type: "application/msword",
    });
    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });
    expect(mockApi).not.toHaveBeenCalled();
    expect(screen.queryByText("Resume submitted!")).not.toBeInTheDocument();
  });
});
