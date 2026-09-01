import type { ApiResponse } from "../../types/api";
import type { ProcessingJob } from "../../types/evidence";
import type {
  FusionAnalysisDetail,
  FusionAnalysisRunListData,
  FusionConflict,
  FusionSignalsData,
  JuryAssessment,
} from "../../types/fusion";
import { apiClient } from "./client";

export const fusionService = {
  analyze: (evidenceId: string) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${evidenceId}/fusion-analysis`,
      {},
    ),
  listRuns: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<FusionAnalysisRunListData>>(
      `/evidence/${evidenceId}/fusion-analysis?limit=${limit}&offset=${offset}`,
    ),
  getLatest: (evidenceId: string) =>
    apiClient.get<ApiResponse<FusionAnalysisDetail>>(
      `/evidence/${evidenceId}/fusion-analysis/latest`,
    ),
  getRun: (analysisId: string) =>
    apiClient.get<ApiResponse<FusionAnalysisDetail>>(
      `/fusion-analysis/${analysisId}`,
    ),
  listJury: (evidenceId: string) =>
    apiClient.get<ApiResponse<JuryAssessment[]>>(
      `/evidence/${evidenceId}/fusion-jury`,
    ),
  listConflicts: (evidenceId: string) =>
    apiClient.get<ApiResponse<FusionConflict[]>>(
      `/evidence/${evidenceId}/fusion-conflicts`,
    ),
  getSignals: (evidenceId: string) =>
    apiClient.get<ApiResponse<FusionSignalsData>>(
      `/evidence/${evidenceId}/fusion-signals`,
    ),
};
