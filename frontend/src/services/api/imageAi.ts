import type { ApiResponse } from "../../types/api";
import type {
  ImageAIFindingListData,
  ImageAnalysisRun,
  ImageAnalysisRunListData,
} from "../../types/imageAi";
import type { ProcessingJob } from "../../types/evidence";
import { apiClient } from "./client";

export const imageAiService = {
  analyze: (evidenceId: string) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${evidenceId}/image-analysis`,
      {},
    ),
  listRuns: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<ImageAnalysisRunListData>>(
      `/evidence/${evidenceId}/image-analysis?limit=${limit}&offset=${offset}`,
    ),
  getRun: (analysisId: string) =>
    apiClient.get<ApiResponse<ImageAnalysisRun>>(
      `/image-analysis/${analysisId}`,
    ),
  listFindings: (
    evidenceId: string,
    limit = 100,
    offset = 0,
    detector?: string,
  ) => {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    if (detector) {
      params.set("detector", detector);
    }
    return apiClient.get<ApiResponse<ImageAIFindingListData>>(
      `/evidence/${evidenceId}/image-findings?${params.toString()}`,
    );
  },
};
