import type { ApiResponse } from "../../types/api";
import type {
  DocumentAIFindingListData,
  DocumentAnalysisRunListData,
} from "../../types/documentAi";
import type { ProcessingJob } from "../../types/evidence";
import { apiClient } from "./client";

export const documentAiService = {
  analyze: (evidenceId: string) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${evidenceId}/document-analysis`,
      {},
    ),
  listRuns: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<DocumentAnalysisRunListData>>(
      `/evidence/${evidenceId}/document-analysis?limit=${limit}&offset=${offset}`,
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
    return apiClient.get<ApiResponse<DocumentAIFindingListData>>(
      `/evidence/${evidenceId}/document-findings?${params.toString()}`,
    );
  },
};
