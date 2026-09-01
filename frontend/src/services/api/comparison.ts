import type { ApiResponse } from "../../types/api";
import type { ProcessingJob } from "../../types/evidence";
import type {
  ComparisonRun,
  ComparisonRunListData,
  ComparisonSummary,
  DifferenceListData,
  ReferenceEvidence,
  ReferenceEvidenceListData,
} from "../../types/comparison";
import { apiClient } from "./client";

export const comparisonService = {
  registerReference: (
    caseId: string,
    payload: { evidence_id: string; label: string; description?: string },
  ) =>
    apiClient.postJson<ApiResponse<ReferenceEvidence>>(
      `/cases/${caseId}/references`,
      payload,
    ),
  listReferences: (caseId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<ReferenceEvidenceListData>>(
      `/cases/${caseId}/references?limit=${limit}&offset=${offset}`,
    ),
  compare: (evidenceId: string, referenceEvidenceId: string) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${evidenceId}/compare`,
      { reference_evidence_id: referenceEvidenceId },
    ),
  listComparisons: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<ComparisonRunListData>>(
      `/evidence/${evidenceId}/comparisons?limit=${limit}&offset=${offset}`,
    ),
  getComparison: (comparisonId: string) =>
    apiClient.get<ApiResponse<ComparisonRun>>(
      `/comparisons/${comparisonId}`,
    ),
  listDifferences: (evidenceId: string, limit = 100, offset = 0) =>
    apiClient.get<ApiResponse<DifferenceListData>>(
      `/evidence/${evidenceId}/differences?limit=${limit}&offset=${offset}`,
    ),
  summary: (evidenceId: string) =>
    apiClient.get<ApiResponse<ComparisonSummary>>(
      `/evidence/${evidenceId}/comparison-summary`,
    ),
};
