import {
  saveSession,
  getToken,
  getUser,
  clearSession,
  isLoggedIn,
  type SessionUser,
} from "@/lib/auth/session";

const TOKEN_KEY = "skillshub_jwt";
const USER_KEY = "skillshub_user";

const mockUser: SessionUser = {
  id: "user-1",
  email: "test@example.com",
  name: "Test User",
  role: "hr",
};

beforeEach(() => {
  localStorage.clear();
});

describe("saveSession", () => {
  it("stores token in localStorage", () => {
    saveSession("my-token", mockUser);
    expect(localStorage.getItem(TOKEN_KEY)).toBe("my-token");
  });

  it("stores serialized user in localStorage", () => {
    saveSession("my-token", mockUser);
    expect(JSON.parse(localStorage.getItem(USER_KEY)!)).toEqual(mockUser);
  });
});

describe("getToken", () => {
  it("returns null when no token stored", () => {
    expect(getToken()).toBeNull();
  });

  it("returns stored token", () => {
    localStorage.setItem(TOKEN_KEY, "abc123");
    expect(getToken()).toBe("abc123");
  });
});

describe("getUser", () => {
  it("returns null when no user stored", () => {
    expect(getUser()).toBeNull();
  });

  it("returns parsed user object", () => {
    localStorage.setItem(USER_KEY, JSON.stringify(mockUser));
    expect(getUser()).toEqual(mockUser);
  });

  it("returns null for corrupted JSON", () => {
    localStorage.setItem(USER_KEY, "not-valid-json{{{");
    expect(getUser()).toBeNull();
  });

  it("returns null for empty string", () => {
    localStorage.setItem(USER_KEY, "");
    expect(getUser()).toBeNull();
  });
});

describe("clearSession", () => {
  it("removes token and user from localStorage", () => {
    saveSession("tok", mockUser);
    clearSession();
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
    expect(localStorage.getItem(USER_KEY)).toBeNull();
  });

  it("is safe to call when nothing is stored", () => {
    expect(() => clearSession()).not.toThrow();
  });
});

describe("isLoggedIn", () => {
  it("returns false when no token", () => {
    expect(isLoggedIn()).toBe(false);
  });

  it("returns true when token exists", () => {
    localStorage.setItem(TOKEN_KEY, "some-jwt");
    expect(isLoggedIn()).toBe(true);
  });

  it("returns false after clearSession", () => {
    saveSession("tok", mockUser);
    clearSession();
    expect(isLoggedIn()).toBe(false);
  });
});
