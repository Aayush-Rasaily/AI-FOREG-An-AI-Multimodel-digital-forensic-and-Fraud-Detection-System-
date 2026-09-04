import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  EvidenceGap,
  Hypothesis,
  IntelligenceRecommendation,
  IntelligenceRun,
  InvestigationCaseSummary,
} from "../../types/investigationIntelligence";

export const investigationIntelligenceApi = {
  analyze: (caseId: string) =>
    apiClient.postJson<ApiResponse<IntelligenceRun>>(
      `/cases/${caseId}/investigation-intelligence`,
      {},
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<IntelligenceRun>>(
      `/cases/${caseId}/investigation-intelligence`,
    ),
  preview: (caseId: string) =>
    apiClient.get<ApiResponse<IntelligenceRun>>(
      `/cases/${caseId}/investigation-preview`,
    ),
  getRun: (runId: string) =>
    apiClient.get<ApiResponse<IntelligenceRun>>(
      `/investigation-intelligence/${runId}`,
    ),
  listHypotheses: (caseId: string) =>
    apiClient.get<ApiResponse<{ items: Hypothesis[]; total: number }>>(
      `/cases/${caseId}/hypotheses`,
    ),
  listGaps: (caseId: string) =>
    apiClient.get<ApiResponse<{ items: EvidenceGap[]; total: number }>>(
      `/cases/${caseId}/evidence-gaps`,
    ),
  listRecommendations: (caseId: string) =>
    apiClient.get<
      ApiResponse<{ items: IntelligenceRecommendation[]; total: number }>
    >(`/cases/${caseId}/recommendations`),
  getSummary: (caseId: string) =>
    apiClient.get<ApiResponse<InvestigationCaseSummary>>(
      `/cases/${caseId}/investigation-summary`,
    ),
};
