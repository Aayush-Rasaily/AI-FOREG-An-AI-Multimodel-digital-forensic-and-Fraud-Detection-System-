import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  MonitoringDashboard,
  MonitoringRefresh,
  MonitoringSection,
  SystemHealth,
} from "../../types/monitoring";

export const monitoringApi = {
  dashboard() {
    return apiClient.get<ApiResponse<MonitoringDashboard>>(
      "/monitoring/dashboard",
    );
  },
  systemHealth() {
    return apiClient.get<ApiResponse<SystemHealth>>(
      "/monitoring/system-health",
    );
  },
  processing() {
    return apiClient.get<ApiResponse<MonitoringSection>>(
      "/monitoring/processing",
    );
  },
  ai() {
    return apiClient.get<ApiResponse<MonitoringSection>>("/monitoring/ai");
  },
  apiUsage() {
    return apiClient.get<ApiResponse<MonitoringSection>>("/monitoring/api");
  },
  activity() {
    return apiClient.get<ApiResponse<MonitoringSection>>(
      "/monitoring/activity",
    );
  },
  bottlenecks() {
    return apiClient.get<ApiResponse<MonitoringSection>>(
      "/monitoring/bottlenecks",
    );
  },
  auditSummary() {
    return apiClient.get<ApiResponse<MonitoringSection>>(
      "/monitoring/audit-summary",
    );
  },
  refresh() {
    return apiClient.postJson<ApiResponse<MonitoringRefresh>>(
      "/monitoring/refresh",
      {},
    );
  },
};
