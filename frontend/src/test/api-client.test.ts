import { beforeEach, describe, expect, it, vi } from "vitest";

import { appConfig } from "../config/env";
import { ApiClient, ApiClientError } from "../services/api/client";

describe("API client", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true, data: { status: "healthy" } }),
      }),
    );
  });

  it("uses the configured relative API base URL by default", () => {
    expect(appConfig.apiBaseUrl).toBe("/api/v1");
    expect(appConfig.apiBaseUrl).not.toContain("localhost");
  });

  it("translates API errors without exposing raw response details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        headers: new Headers({ "X-Request-ID": "request-123" }),
        json: async () => ({
          success: false,
          error: {
            code: "DATABASE_UNAVAILABLE",
            message: "Service unavailable",
            request_id: "request-123",
          },
        }),
      }),
    );

    await expect(new ApiClient().get("/health")).rejects.toMatchObject({
      code: "DATABASE_UNAVAILABLE",
      status: 503,
      requestId: "request-123",
    } satisfies Partial<ApiClientError>);
  });
});

