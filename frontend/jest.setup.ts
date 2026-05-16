import "@testing-library/jest-dom";

// ─── next/navigation global mock ─────────────────────────────────────────────
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  })),
  useParams: jest.fn(() => ({})),
  useSearchParams: jest.fn(() => new URLSearchParams()),
  usePathname: jest.fn(() => "/"),
}));

// ─── next/link global mock ────────────────────────────────────────────────────
jest.mock("next/link", () => {
  function MockLink(props: {
    children: React.ReactNode;
    href: unknown;
    [key: string]: unknown;
  }) {
    const { children, href, ...rest } = props;
    return require("react").createElement(
      "a",
      { href: typeof href === "string" ? href : String(href), ...rest },
      children
    );
  }
  MockLink.displayName = "MockLink";
  return MockLink;
});

// ─── Sonner toasts mock ───────────────────────────────────────────────────────
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
  },
  Toaster: () => null,
}));

// ─── window.matchMedia (ThemeToggle / Tailwind dark mode) ────────────────────
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// ─── DOM stubs ────────────────────────────────────────────────────────────────
window.HTMLElement.prototype.scrollIntoView = jest.fn();

global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as unknown as typeof IntersectionObserver;

// ─── window.location (logout redirect) ───────────────────────────────────────
Object.defineProperty(window, "location", {
  writable: true,
  value: { href: "", assign: jest.fn(), replace: jest.fn() },
});

// ─── Reset per-test ───────────────────────────────────────────────────────────
afterEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
});
