import React from "react";
import { render } from "@testing-library/react";
import {
  Skeleton,
  SkeletonCard,
  SkeletonProfile,
  SkeletonTable,
} from "@/components/ui/Skeleton";

describe("Skeleton", () => {
  it("renders a div with skeleton class", () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toHaveClass("skeleton");
  });

  it("accepts and applies className", () => {
    const { container } = render(<Skeleton className="h-4 w-32" />);
    expect(container.firstChild).toHaveClass("h-4", "w-32", "skeleton");
  });
});

describe("SkeletonCard", () => {
  it("renders without error", () => {
    const { container } = render(<SkeletonCard />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("contains multiple skeleton elements", () => {
    const { container } = render(<SkeletonCard />);
    const skeletons = container.querySelectorAll(".skeleton");
    expect(skeletons.length).toBeGreaterThan(1);
  });

  it("accepts className", () => {
    const { container } = render(<SkeletonCard className="custom" />);
    expect(container.firstChild).toHaveClass("custom");
  });
});

describe("SkeletonProfile", () => {
  it("renders without error", () => {
    const { container } = render(<SkeletonProfile />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("renders multiple skeleton chips (simulating skills)", () => {
    const { container } = render(<SkeletonProfile />);
    const roundedFull = container.querySelectorAll(".rounded-full.skeleton");
    expect(roundedFull.length).toBeGreaterThan(0);
  });
});

describe("SkeletonTable", () => {
  it("renders 4 rows by default", () => {
    const { container } = render(<SkeletonTable />);
    const rows = container.querySelectorAll(".rounded-xl");
    expect(rows.length).toBe(4);
  });

  it("renders custom number of rows", () => {
    const { container } = render(<SkeletonTable rows={7} />);
    const rows = container.querySelectorAll(".rounded-xl");
    expect(rows.length).toBe(7);
  });

  it("renders 1 row", () => {
    const { container } = render(<SkeletonTable rows={1} />);
    const rows = container.querySelectorAll(".rounded-xl");
    expect(rows.length).toBe(1);
  });
});
