import React from "react";
import { render, screen } from "@testing-library/react";
import { SkillChip } from "@/components/skills/SkillChip";

describe("SkillChip", () => {
  it("renders the skill name", () => {
    render(<SkillChip name="React" />);
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  it("renders years suffix when years provided", () => {
    render(<SkillChip name="React" years={5} />);
    expect(screen.getByText("5y")).toBeInTheDocument();
  });

  it("does not render years suffix when years is null", () => {
    render(<SkillChip name="React" years={null} />);
    expect(screen.queryByText(/y$/)).not.toBeInTheDocument();
  });

  it("renders sparkle emoji for inferred skills", () => {
    render(<SkillChip name="React" inferred />);
    expect(screen.getByText("✨")).toBeInTheDocument();
  });

  it("does not render sparkle emoji when not inferred", () => {
    render(<SkillChip name="React" />);
    expect(screen.queryByText("✨")).not.toBeInTheDocument();
  });

  it("renders GitHub SVG icon for github source", () => {
    const { container } = render(<SkillChip name="React" fromGithub />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  it("does not render GitHub SVG when fromGithub is false", () => {
    const { container } = render(<SkillChip name="React" fromGithub={false} />);
    expect(container.querySelector("svg")).not.toBeInTheDocument();
  });

  it("renders proficiency dot for expert", () => {
    const { container } = render(<SkillChip name="React" proficiency="expert" />);
    const dot = container.querySelector(".bg-emerald-500");
    expect(dot).toBeInTheDocument();
  });

  it("renders proficiency dot for intermediate", () => {
    const { container } = render(<SkillChip name="React" proficiency="intermediate" />);
    const dot = container.querySelector(".bg-amber-400");
    expect(dot).toBeInTheDocument();
  });

  it("renders proficiency dot for novice", () => {
    const { container } = render(<SkillChip name="React" proficiency="novice" />);
    const dot = container.querySelector(".bg-slate-300");
    expect(dot).toBeInTheDocument();
  });

  it("does not render dot when no proficiency", () => {
    render(<SkillChip name="React" />);
    // no dot span rendered
    const chip = screen.getByText("React").closest("span")!;
    const spans = chip.querySelectorAll("span");
    expect(spans.length).toBe(0);
  });

  it("builds title attribute with proficiency and years", () => {
    render(<SkillChip name="React" proficiency="expert" years={5} />);
    expect(screen.getByTitle("expert · 5y")).toBeInTheDocument();
  });

  it("builds title with inferred flag", () => {
    render(<SkillChip name="React" proficiency="intermediate" inferred />);
    expect(screen.getByTitle("intermediate · inferred")).toBeInTheDocument();
  });

  it("builds title with fromGithub flag", () => {
    render(<SkillChip name="React" fromGithub />);
    expect(screen.getByTitle("from GitHub")).toBeInTheDocument();
  });

  it("applies language category styles", () => {
    const { container } = render(<SkillChip name="TypeScript" category="language" />);
    expect(container.firstChild).toHaveClass("bg-blue-50");
  });

  it("applies framework category styles", () => {
    const { container } = render(<SkillChip name="React" category="framework" />);
    expect(container.firstChild).toHaveClass("bg-violet-50");
  });

  it("falls back to tool styles for unknown category", () => {
    const { container } = render(<SkillChip name="Something" category="unknown" />);
    expect(container.firstChild).toHaveClass("bg-slate-50");
  });

  it("accepts additional className", () => {
    const { container } = render(<SkillChip name="React" className="my-custom-class" />);
    expect(container.firstChild).toHaveClass("my-custom-class");
  });
});
