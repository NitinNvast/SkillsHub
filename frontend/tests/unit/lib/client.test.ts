import { api, ApiError } from "@/lib/api/client";

const API_URL = "http://localhost:8000";

beforeEach(() => {
  localStorage.clear();
  jest.resetAllMocks();
});

describe("ApiError", () => {
  it("extends Error", () => {
    const err = new ApiError(404, "Not found");
    expect(err).toBeInstanceOf(Error);
  });

  it("stores status and message", () => {
    const err = new ApiError(401, "Unauthorized");
    expect(err.status).toBe(401);
    expect(err.message).toBe("Unauthorized");
  });

  it("stores detail payload", () => {
    const detail = { field: "email", msg: "invalid" };
    const err = new ApiError(422, "Validation error", detail);
    expect(err.detail).toEqual(detail);
  });
});

describe("api()", () => {
  const mockFetch = jest.fn();

  beforeEach(() => {
    global.fetch = mockFetch;
  });

  function mockResponse(body: unknown, status = 200) {
    const text = JSON.stringify(body);
    mockFetch.mockResolvedValueOnce({
      ok: status >= 200 && status < 300,
      status,
      statusText: status === 200 ? "OK" : "Error",
      text: async () => text,
    });
  }

  it("prefixes API_URL to the path", async () => {
    mockResponse({ result: true });
    await api("/test-path");
    expect(mockFetch).toHaveBeenCalledWith(
      `${API_URL}/test-path`,
      expect.any(Object)
    );
  });

  it("sets Accept: application/json header", async () => {
    mockResponse({});
    await api("/test");
    const headers: Headers = mockFetch.mock.calls[0][1].headers;
    expect(headers.get("Accept")).toBe("application/json");
  });

  it("sets Content-Type: application/json for JSON body", async () => {
    mockResponse({});
    await api("/test", { method: "POST", body: JSON.stringify({ x: 1 }) });
    const headers: Headers = mockFetch.mock.calls[0][1].headers;
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("does NOT set Content-Type for FormData body", async () => {
    mockResponse({});
    const fd = new FormData();
    await api("/upload", { method: "POST", body: fd });
    const headers: Headers = mockFetch.mock.calls[0][1].headers;
    expect(headers.get("Content-Type")).toBeNull();
  });

  it("attaches JWT from localStorage as Authorization header", async () => {
    localStorage.setItem("skillshub_jwt", "test-jwt-token");
    mockResponse({});
    await api("/secure");
    const headers: Headers = mockFetch.mock.calls[0][1].headers;
    expect(headers.get("Authorization")).toBe("Bearer test-jwt-token");
  });

  it("uses explicitly-passed token over localStorage", async () => {
    localStorage.setItem("skillshub_jwt", "stored-token");
    mockResponse({});
    await api("/secure", {}, "explicit-token");
    const headers: Headers = mockFetch.mock.calls[0][1].headers;
    expect(headers.get("Authorization")).toBe("Bearer explicit-token");
  });

  it("omits Authorization when no token present", async () => {
    mockResponse({});
    await api("/public");
    const headers: Headers = mockFetch.mock.calls[0][1].headers;
    expect(headers.get("Authorization")).toBeNull();
  });

  it("returns parsed JSON on 2xx response", async () => {
    mockResponse({ hello: "world" });
    const result = await api<{ hello: string }>("/data");
    expect(result).toEqual({ hello: "world" });
  });

  it("returns null for empty response body", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
      statusText: "No Content",
      text: async () => "",
    });
    const result = await api("/empty");
    expect(result).toBeNull();
  });

  it("throws ApiError with status and message on 4xx", async () => {
    mockResponse({ detail: "Unauthorized" }, 401);
    const err = await api("/secure").catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 401, message: "Unauthorized" });
  });

  it("throws ApiError on 500", async () => {
    mockResponse({ detail: "Internal Server Error" }, 500);
    await expect(api("/broken")).rejects.toMatchObject({ status: 500 });
  });

  it("falls back to statusText when no detail in error body", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
      text: async () => JSON.stringify({}),
    });
    await expect(api("/down")).rejects.toMatchObject({
      status: 503,
      message: "Service Unavailable",
    });
  });
});
