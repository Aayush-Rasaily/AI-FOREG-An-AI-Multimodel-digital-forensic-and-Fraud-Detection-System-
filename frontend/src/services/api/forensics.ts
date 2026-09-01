import type { ApiResponse } from "../../types/api";
import type { ArtifactListData, ProcessingJob } from "../../types/evidence";
import type {
  AnalysisRun,
  AnalysisRunListData,
  AnalysisSummary,
  FindingListData,
} from "../../types/forensics";
import { apiClient } from "./client";

export const forensicsService = {
  analyze: (evidenceId: string) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${evidenceId}/analyze`,
      {},
    ),
  listAnalysis: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<AnalysisRunListData>>(
      `/evidence/${evidenceId}/analysis?limit=${limit}&offset=${offset}`,
    ),
  getAnalysisRun: (analysisId: string) =>
    apiClient.get<ApiResponse<AnalysisRun>>(
      `/analysis/${analysisId}`,
    ),
  listFindings: (evidenceId: string, limit = 100, offset = 0) =>
    apiClient.get<ApiResponse<FindingListData>>(
      `/evidence/${evidenceId}/findings?limit=${limit}&offset=${offset}`,
    ),
  listHeatmaps: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<ArtifactListData>>(
      `/evidence/${evidenceId}/heatmaps?limit=${limit}&offset=${offset}`,
    ),
  summary: (evidenceId: string) =>
    apiClient.get<ApiResponse<AnalysisSummary>>(
      `/evidence/${evidenceId}/analysis-summary`,
    ),
};
