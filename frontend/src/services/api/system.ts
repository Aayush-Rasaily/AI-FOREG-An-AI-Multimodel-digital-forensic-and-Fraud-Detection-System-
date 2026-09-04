import type { ApiResponse } from "../../types/api";
import type {
  DiagnosticsResult,
  DiagnosticsRun,
  HealthSnapshot,
  JobsSummary,
  StorageStats,
  SystemConfiguration,
  SystemLiveness,
  SystemMetrics,
  SystemReadiness,
  SystemReleaseCheck,
  SystemReleaseInfo,
  SystemStartupValidation,
  SystemValidationResult,
  SystemVersionInfo,
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
  getVersion: () =>
    apiClient.get<ApiResponse<SystemVersionInfo>>("/system/version"),
  getRelease: () =>
    apiClient.get<ApiResponse<SystemReleaseInfo>>("/system/release"),
  getLiveness: () =>
    apiClient.get<ApiResponse<SystemLiveness>>("/system/liveness"),
  getReadiness: () =>
    apiClient.get<ApiResponse<SystemReadiness>>("/system/readiness"),
  getStartupValidation: () =>
    apiClient.get<ApiResponse<SystemStartupValidation>>(
      "/system/startup-validation",
    ),
  getConfiguration: () =>
    apiClient.get<ApiResponse<SystemConfiguration>>("/system/configuration"),
  validate: () =>
    apiClient.postJson<ApiResponse<SystemValidationResult>>(
      "/system/validate",
      {},
    ),
  releaseCheck: () =>
    apiClient.postJson<ApiResponse<SystemReleaseCheck>>(
      "/system/release-check",
      {},
    ),
};
