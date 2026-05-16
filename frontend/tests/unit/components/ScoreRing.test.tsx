import React from "react";
import { render, screen } from "@testing-library/react";
import { ScoreRing } from "@/components/search/ScoreRing";

describe("ScoreRing", () => {
  it("renders the score number", () => {
    render(<ScoreRing score={85} />);
    expect(screen.getByText("85")).toBeInTheDocument();
  });

  it("renders score 0", () => {
    render(<ScoreRing score={0} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders score 100", () => {
    render(<ScoreRing score={100} />);
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("uses green color for score >= 85", () => {
    render(<ScoreRing score={90} />);
    const score = screen.getByText("90");
    expect(score).toHaveStyle({ color: "#22c55e" });
  });

  it("uses amber color for score >= 65 and < 85", () => {
    render(<ScoreRing score={75} />);
    const score = screen.getByText("75");
    expect(score).toHaveStyle({ color: "#f59e0b" });
  });

  it("uses red color for score < 65", () => {
    render(<ScoreRing score={40} />);
    const score = screen.getByText("40");
    expect(score).toHaveStyle({ color: "#ef4444" });
  });

  it("uses green at exactly 85", () => {
    render(<ScoreRing score={85} />);
    expect(screen.getByText("85")).toHaveStyle({ color: "#22c55e" });
  });

  it("uses amber at exactly 65", () => {
    render(<ScoreRing score={65} />);
    expect(screen.getByText("65")).toHaveStyle({ color: "#f59e0b" });
  });

  it("renders SVG circles", () => {
    const { container } = render(<ScoreRing score={80} />);
    const circles = container.querySelectorAll("circle");
    expect(circles.length).toBe(2);
  });

  it("applies default size 60", () => {
    const { container } = render(<ScoreRing score={70} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveStyle({ width: "60px", height: "60px" });
  });

  it("applies custom size prop", () => {
    const { container } = render(<ScoreRing score={70} size={80} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveStyle({ width: "80px", height: "80px" });
  });

  it("sets correct SVG dimensions from size prop", () => {
    const { container } = render(<ScoreRing score={70} size={90} />);
    const svg = container.querySelector("svg")!;
    expect(svg.getAttribute("width")).toBe("90");
    expect(svg.getAttribute("height")).toBe("90");
  });
});
