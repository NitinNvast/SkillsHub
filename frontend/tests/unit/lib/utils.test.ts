import { cn } from "@/lib/utils";

describe("cn()", () => {
  it("returns a single class string unchanged", () => {
    expect(cn("foo")).toBe("foo");
  });

  it("joins multiple class strings", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("ignores falsy values", () => {
    expect(cn("foo", false, null, undefined, "bar")).toBe("foo bar");
  });

  it("handles conditional objects", () => {
    expect(cn({ active: true, disabled: false })).toBe("active");
  });

  it("merges conflicting Tailwind classes (last wins)", () => {
    const result = cn("px-2", "px-4");
    expect(result).toBe("px-4");
  });

  it("merges bg-red and bg-blue — last wins", () => {
    const result = cn("bg-red-500", "bg-blue-500");
    expect(result).toBe("bg-blue-500");
  });

  it("handles array inputs", () => {
    expect(cn(["foo", "bar"])).toBe("foo bar");
  });

  it("returns empty string for no inputs", () => {
    expect(cn()).toBe("");
  });

  it("handles mixed conditional and string inputs", () => {
    const active = true;
    const result = cn("base", active && "active", !active && "inactive");
    expect(result).toBe("base active");
  });
});
