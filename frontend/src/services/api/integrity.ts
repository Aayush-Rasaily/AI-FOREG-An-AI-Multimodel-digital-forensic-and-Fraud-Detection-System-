import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  IntegrityAlert,
  IntegrityDrift,
  IntegrityHistoryItem,
  IntegrityRun,
} from "../../types/integrity";

export const integrityApi = {
  runCheck: (caseId: string) =>
    apiClient.postJson<ApiResponse<IntegrityRun>>(
      `/cases/${caseId}/integrity-check`,
      {},
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<IntegrityRun>>(`/cases/${caseId}/integrity`),
  preview: (caseId: string) =>
    apiClient.get<ApiResponse<IntegrityRun>>(
      `/cases/${caseId}/integrity/preview`,
    ),
  getRun: (runId: string) =>
    apiClient.get<ApiResponse<IntegrityRun>>(`/integrity/${runId}`),
  listAlerts: (caseId: string) =>
    apiClient.get<ApiResponse<{ items: IntegrityAlert[]; total: number }>>(
      `/cases/${caseId}/integrity/alerts`,
    ),
  listDrift: (caseId: string) =>
    apiClient.get<ApiResponse<{ items: IntegrityDrift[]; total: number }>>(
      `/cases/${caseId}/integrity/drift`,
    ),
  getHistory: (caseId: string) =>
    apiClient.get<
      ApiResponse<{ items: IntegrityHistoryItem[]; total: number }>
    >(`/cases/${caseId}/integrity/history`),
};
