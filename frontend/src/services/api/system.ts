import type { ApiResponse } from "../../types/api";
import type {
  DiagnosticsResult,
  DiagnosticsRun,
  HealthSnapshot,
  JobsSummary,
  StorageStats,
  SystemMetrics,
} from "../../types/system";
import { apiClient } from "./client";

export const systemService = {
  getHealth: () =>
    apiClient.get<ApiResponse<HealthSnapshot>>("/system/health"),
  getMetrics: () =>
    apiClient.get<ApiResponse<SystemMetrics>>("/system/metrics"),
  getJobs: () =>
    apiClient.get<ApiResponse<JobsSummary>>("/system/jobs"),
  getStorage: () =>
    apiClient.get<ApiResponse<StorageStats>>("/system/storage"),
  getDiagnostics: () =>
    apiClient.get<ApiResponse<DiagnosticsResult>>("/system/diagnostics"),
  runDiagnostics: () =>
    apiClient.postJson<ApiResponse<DiagnosticsRun>>(
      "/system/diagnostics/run",
      {},
    ),
};
