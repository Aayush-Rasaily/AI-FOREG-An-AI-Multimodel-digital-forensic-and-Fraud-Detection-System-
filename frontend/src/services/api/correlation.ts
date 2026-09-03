import type { ApiResponse } from "../../types/api";
import type {
  CorrelationDetail,
  CorrelationRun,
  CorrelationRunListData,
  EvidenceCorrelation,
} from "../../types/correlation";
import { apiClient } from "./client";

export const correlationService = {
  generate: (caseId: string) =>
    apiClient.postJson<ApiResponse<CorrelationRun>>(
      `/cases/${caseId}/correlations`,
      {},
    ),
  listRuns: (caseId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<CorrelationRunListData>>(
      `/cases/${caseId}/correlations?limit=${limit}&offset=${offset}`,
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<CorrelationDetail>>(
      `/cases/${caseId}/correlations/latest`,
    ),
  listForEvidence: (evidenceId: string) =>
    apiClient.get<ApiResponse<EvidenceCorrelation[]>>(
      `/evidence/${evidenceId}/correlations`,
    ),
  getCorrelation: (correlationId: string) =>
    apiClient.get<ApiResponse<EvidenceCorrelation>>(
      `/correlations/${correlationId}`,
    ),
};
