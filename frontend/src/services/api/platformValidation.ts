import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  HealthReport,
  PlatformReadiness,
  PlatformValidationRun,
  ValidationList,
} from "../../types/platformValidation";

export const platformValidationApi = {
  validate: () =>
    apiClient.postJson<ApiResponse<PlatformValidationRun>>(
      "/platform/validate",
      {},
    ),
  list: () =>
    apiClient.get<ApiResponse<ValidationList>>("/platform/validation"),
  getLatest: () =>
    apiClient.get<ApiResponse<PlatformValidationRun>>(
      "/platform/validation/latest",
    ),
  getRun: (runId: string) =>
    apiClient.get<ApiResponse<PlatformValidationRun>>(
      `/platform/validation/${runId}`,
    ),
  getReadiness: () =>
    apiClient.get<ApiResponse<PlatformReadiness>>("/platform/readiness"),
  getHealthReport: () =>
    apiClient.get<ApiResponse<HealthReport>>("/platform/health/report"),
};
