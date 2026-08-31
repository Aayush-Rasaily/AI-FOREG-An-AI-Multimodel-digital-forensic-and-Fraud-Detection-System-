import { apiClient } from "./client";
import type { ApiResponse, HealthStatus, SystemInfo } from "../../types/api";

export const healthService = {
  getHealth: (signal?: AbortSignal) =>
    apiClient.get<ApiResponse<HealthStatus>>("/health", signal),
  getSystemInfo: (signal?: AbortSignal) =>
    apiClient.get<ApiResponse<SystemInfo>>("/system/info", signal),
};

