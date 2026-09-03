import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  InvestigationSummary,
  InvestigationSummaryList,
} from "../../types/intelligence";

export const intelligenceApi = {
  generate(caseId: string) {
    return apiClient.postJson<ApiResponse<InvestigationSummary>>(
      `/cases/${caseId}/investigation-summaries`,
      {},
    );
  },
  list(caseId: string, limit = 50, offset = 0) {
    return apiClient.get<ApiResponse<InvestigationSummaryList>>(
      `/cases/${caseId}/investigation-summaries?limit=${limit}&offset=${offset}`,
    );
  },
  latest(caseId: string) {
    return apiClient.get<ApiResponse<InvestigationSummary>>(
      `/cases/${caseId}/investigation-summaries/latest`,
    );
  },
  get(summaryId: string) {
    return apiClient.get<ApiResponse<InvestigationSummary>>(
      `/investigation-summaries/${summaryId}`,
    );
  },
};
