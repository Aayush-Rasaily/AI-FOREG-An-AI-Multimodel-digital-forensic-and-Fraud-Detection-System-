export interface ApiResponse<T> {
  success: true;
  data: T;
  request_id: string | null;
  timestamp: string;
}

export interface ApiErrorBody {
  success: false;
  error: {
    code: string;
    message: string;
    request_id: string | null;
    details?: Record<string, unknown> | null;
  };
}

export interface HealthStatus {
  status: "healthy" | "degraded";
  version: string;
  environment: string;
  database: "healthy" | "unavailable";
  timestamp: string;
}

export interface SystemInfo {
  service: string;
  version: string;
  environment: string;
  python_version: string;
  platform: string;
}

