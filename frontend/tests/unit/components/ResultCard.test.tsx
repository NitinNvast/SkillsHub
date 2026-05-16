import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ResultCard } from "@/components/search/ResultCard";
import { mockSearchResult } from "@/tests/mocks/data";

const baseResult = mockSearchResult;

describe("ResultCard", () => {
  it("renders employee name as a link", () => {
    render(<ResultCard result={baseResult} rank={1} />);
    const link = screen.getByRole("link", { name: /jane smith/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", `/employees/${baseResult.employee_id}`);
  });

  it("renders the rank number", () => {
    render(<ResultCard result={baseResult} rank={3} />);
    expect(screen.getByText("#3")).toBeInTheDocument();
  });

  it("renders ScoreRing with match score", () => {
    render(<ResultCard result={baseResult} rank={1} />);
    expect(screen.getByText(String(baseResult.match_score))).toBeInTheDocument();
  });

  it("renders the AI reasoning text", () => {
    render(<ResultCard result={baseResult} rank={1} />);
    expect(screen.getByText(baseResult.reasoning)).toBeInTheDocument();
  });

  it("renders title and location when provided", () => {
    render(<ResultCard result={baseResult} rank={1} />);
    expect(screen.getByText(baseResult.title!)).toBeInTheDocument();
    expect(screen.getByText(baseResult.location!)).toBeInTheDocument();
  });

  it("does not render title when null", () => {
    const result = { ...baseResult, title: null };
    render(<ResultCard result={result} rank={1} />);
    expect(screen.queryByText("Senior Software Engineer")).not.toBeInTheDocument();
  });

  it("does not render location when null", () => {
    const result = { ...baseResult, location: null };
    render(<ResultCard result={result} rank={1} />);
    expect(screen.queryByText("San Francisco, CA")).not.toBeInTheDocument();
  });

  it("shows 'Available' badge for available status", () => {
    render(<ResultCard result={baseResult} rank={1} />);
    expect(screen.getByText("Available")).toBeInTheDocument();
  });

  it("shows 'Partially available' badge for partial status", () => {
    const result = { ...baseResult, availability: "partial" };
    render(<ResultCard result={result} rank={1} />);
    expect(screen.getByText("Partially available")).toBeInTheDocument();
  });

  it("shows 'Allocated' for unknown availability", () => {
    const result = { ...baseResult, availability: "unknown-status" };
    render(<ResultCard result={result} rank={1} />);
    expect(screen.getByText("Allocated")).toBeInTheDocument();
  });

  it("renders top skill chips", () => {
    render(<ResultCard result={baseResult} rank={1} />);
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  it("does not render skills section when top_skills is empty", () => {
    const result = { ...baseResult, top_skills: [] };
    render(<ResultCard result={result} rank={1} />);
    // Only the name chip in the result should be gone; reasoning still visible
    expect(screen.queryByTitle(/expert/)).not.toBeInTheDocument();
  });

  it("shows 'Show strengths & gaps' button when data exists", () => {
    render(<ResultCard result={baseResult} rank={1} />);
    expect(screen.getByText(/show strengths & gaps/i)).toBeInTheDocument();
  });

  it("does NOT show toggle button when strengths and gaps are both empty", () => {
    const result = { ...baseResult, strengths: [], gaps: [] };
    render(<ResultCard result={result} rank={1} />);
    expect(screen.queryByText(/show strengths/i)).not.toBeInTheDocument();
  });

  it("expands to show strengths and gaps on button click", () => {
    render(<ResultCard result={baseResult} rank={1} />);
    const btn = screen.getByText(/show strengths & gaps/i);
    fireEvent.click(btn);
    expect(screen.getByText("Strengths")).toBeInTheDocument();
    expect(screen.getByText("Gaps")).toBeInTheDocument();
    baseResult.strengths.forEach((s) => expect(screen.getByText(s)).toBeInTheDocument());
    baseResult.gaps.forEach((g) => expect(screen.getByText(g)).toBeInTheDocument());
  });

  it("collapses back to 'Show strengths & gaps' on second click", () => {
    render(<ResultCard result={baseResult} rank={1} />);
    const btn = screen.getByText(/show strengths & gaps/i);
    fireEvent.click(btn);
    expect(screen.getByText(/hide details/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/hide details/i));
    expect(screen.getByText(/show strengths & gaps/i)).toBeInTheDocument();
  });

  it("renders only strengths section when gaps is empty", () => {
    const result = { ...baseResult, gaps: [] };
    render(<ResultCard result={result} rank={1} />);
    fireEvent.click(screen.getByText(/show strengths/i));
    expect(screen.getByText("Strengths")).toBeInTheDocument();
    expect(screen.queryByText("Gaps")).not.toBeInTheDocument();
  });

  it("renders only gaps section when strengths is empty", () => {
    const result = { ...baseResult, strengths: [] };
    render(<ResultCard result={result} rank={1} />);
    fireEvent.click(screen.getByText(/show strengths/i));
    expect(screen.queryByText("Strengths")).not.toBeInTheDocument();
    expect(screen.getByText("Gaps")).toBeInTheDocument();
  });
});
