import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  AnalyticsExport,
  AnalyticsRun,
  AnalyticsSection,
} from "../../types/analytics";

export const analyticsApi = {
  refresh: () =>
    apiClient.postJson<ApiResponse<AnalyticsRun>>("/analytics/refresh", {}),
  getLatest: () => apiClient.get<ApiResponse<AnalyticsRun>>("/analytics"),
  getDashboard: () =>
    apiClient.get<ApiResponse<Record<string, unknown>>>("/analytics/dashboard"),
  getCases: () =>
    apiClient.get<ApiResponse<AnalyticsSection>>("/analytics/cases"),
  getEvidence: () =>
    apiClient.get<ApiResponse<AnalyticsSection>>("/analytics/evidence"),
  getAi: () => apiClient.get<ApiResponse<AnalyticsSection>>("/analytics/ai"),
  getWorkflow: () =>
    apiClient.get<ApiResponse<AnalyticsSection>>("/analytics/workflow"),
  getIntegrity: () =>
    apiClient.get<ApiResponse<AnalyticsSection>>("/analytics/integrity"),
  export: () =>
    apiClient.get<ApiResponse<AnalyticsExport>>("/analytics/export"),
};
