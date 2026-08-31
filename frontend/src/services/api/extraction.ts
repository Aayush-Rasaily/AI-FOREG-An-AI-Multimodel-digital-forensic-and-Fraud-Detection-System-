import type { ApiResponse } from "../../types/api";
import type {
  ArtifactListData,
  ExtractionListData,
  ExtractionRecord,
  ProcessingJob,
} from "../../types/evidence";
import { apiClient } from "./client";

export const extractionService = {
  extract: (evidenceId: string) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${evidenceId}/extract`,
      {},
    ),
  list: (evidenceId: string, limit = 100, offset = 0) =>
    apiClient.get<ApiResponse<ExtractionListData>>(
      `/evidence/${evidenceId}/extractions?limit=${limit}&offset=${offset}`,
    ),
  get: (evidenceId: string, extractionId: string) =>
    apiClient.get<ApiResponse<ExtractionRecord>>(
      `/evidence/${evidenceId}/extractions/${extractionId}`,
    ),
  regions: (evidenceId: string, limit = 100, offset = 0) =>
    apiClient.get<ApiResponse<ExtractionListData>>(
      `/evidence/${evidenceId}/regions?limit=${limit}&offset=${offset}`,
    ),
  artifacts: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<ArtifactListData>>(
      `/evidence/${evidenceId}/extraction-artifacts?limit=${limit}&offset=${offset}`,
    ),
};
