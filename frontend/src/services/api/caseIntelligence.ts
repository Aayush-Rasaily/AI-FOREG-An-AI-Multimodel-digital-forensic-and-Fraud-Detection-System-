import type { ApiResponse } from "../../types/api";
import type {
  CaseConflict,
  CaseIntelligenceDetail,
  CaseIntelligenceRun,
  CaseIntelligenceRunListData,
  CaseRelationship,
  TimelineEvent,
} from "../../types/caseIntelligence";
import { apiClient } from "./client";

export const caseIntelligenceService = {
  analyze: (caseId: string) =>
    apiClient.postJson<ApiResponse<CaseIntelligenceRun>>(
      `/cases/${caseId}/intelligence`,
      {},
    ),
  listRuns: (caseId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<CaseIntelligenceRunListData>>(
      `/cases/${caseId}/intelligence?limit=${limit}&offset=${offset}`,
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<CaseIntelligenceDetail>>(
      `/cases/${caseId}/intelligence/latest`,
    ),
  getRun: (analysisId: string) =>
    apiClient.get<ApiResponse<CaseIntelligenceDetail>>(
      `/case-intelligence/${analysisId}`,
    ),
  listRelationships: (caseId: string) =>
    apiClient.get<ApiResponse<CaseRelationship[]>>(
      `/cases/${caseId}/relationships`,
    ),
  listConflicts: (caseId: string) =>
    apiClient.get<ApiResponse<CaseConflict[]>>(`/cases/${caseId}/conflicts`),
  listTimeline: (caseId: string) =>
    apiClient.get<ApiResponse<TimelineEvent[]>>(
      `/cases/${caseId}/intelligence/timeline`,
    ),
};
