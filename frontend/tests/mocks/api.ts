/**
 * Central API mock helper.
 *
 * Tests call `mockApi(impl)` to configure the `api` function mock for a test.
 * The underlying jest.mock is set up in each test file via:
 *   jest.mock('@/lib/api/client')
 */
import { api } from "@/lib/api/client";

export function mockApiOnce(returnValue: unknown) {
  (api as jest.Mock).mockResolvedValueOnce(returnValue);
}

export function mockApiError(status: number, message: string) {
  const { ApiError } = jest.requireActual("@/lib/api/client");
  (api as jest.Mock).mockRejectedValueOnce(new ApiError(status, message));
}

export function mockApiSequence(...returnValues: unknown[]) {
  returnValues.forEach((v) => (api as jest.Mock).mockResolvedValueOnce(v));
}
