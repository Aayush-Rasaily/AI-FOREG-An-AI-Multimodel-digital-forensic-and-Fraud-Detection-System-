import { appConfig } from "../../config/env";
import type { ApiErrorBody } from "../../types/api";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  hasRememberedSession,
  setTokens,
} from "./tokenStore";

export class ApiClientError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId: string | null;

  constructor(
    message: string,
    status: number,
    code = "NETWORK_ERROR",
    requestId: string | null = null,
  ) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return false;
  }
  try {
    const response = await fetch(`${appConfig.apiBaseUrl}/auth/refresh`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) {
      clearTokens();
      return false;
    }
    const body = (await response.json()) as {
      data: { access_token: string; refresh_token: string };
    };
    setTokens(
      body.data.access_token,
      body.data.refresh_token,
      hasRememberedSession(),
    );
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

export class ApiClient {
  constructor(private readonly baseUrl: string = appConfig.apiBaseUrl) {}

  async get<T>(path: string, signal?: AbortSignal): Promise<T> {
    return this.request<T>(path, { method: "GET", signal });
  }

  async postJson<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    });
  }

  async patchJson<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "PATCH",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    });
  }

  async deleteJson<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "DELETE",
      body: body === undefined ? undefined : JSON.stringify(body),
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
    });
  }

  async postForm<T>(path: string, formData: FormData): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: formData,
    });
  }

  private async request<T>(
    path: string,
    init: RequestInit,
    retried = false,
  ): Promise<T> {
    try {
      const headers = new Headers(init.headers);
      headers.set("Accept", "application/json");
      const token = getAccessToken();
      if (token && !headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${token}`);
      }

      const response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        headers,
      });

      if (
        response.status === 401 &&
        !retried &&
        !path.startsWith("/auth/login") &&
        !path.startsWith("/auth/refresh")
      ) {
        refreshPromise ??= tryRefresh().finally(() => {
          refreshPromise = null;
        });
        const refreshed = await refreshPromise;
        if (refreshed) {
          return this.request<T>(path, init, true);
        }
      }

      if (!response.ok) {
        await this.raiseApiError(response);
      }

      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error;
      }
      throw new ApiClientError(
        "The backend could not be reached. Try again shortly.",
        0,
      );
    }
  }

  private async raiseApiError(response: Response): Promise<never> {
    let body: ApiErrorBody | null = null;
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      body = null;
    }
    throw new ApiClientError(
      body?.error.message || "The backend returned an unexpected error.",
      response.status,
      body?.error.code || "API_ERROR",
      body?.error.request_id || response.headers.get("X-Request-ID"),
    );
  }
}

export const apiClient = new ApiClient();
