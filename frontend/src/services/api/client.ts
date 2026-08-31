import { appConfig } from "../../config/env";
import type { ApiErrorBody } from "../../types/api";

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

  async postForm<T>(path: string, formData: FormData): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: formData,
    });
  }

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        headers: {
          Accept: "application/json",
          ...init.headers,
        },
      });

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

