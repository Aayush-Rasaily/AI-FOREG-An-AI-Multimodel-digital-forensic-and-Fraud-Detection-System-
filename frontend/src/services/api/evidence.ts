import type { ApiResponse } from "../../types/api";
import type { EvidenceListData, EvidenceRecord } from "../../types/evidence";
import { apiClient } from "./client";

export const evidenceService = {
  listForCase: (caseId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<EvidenceListData>>(
      `/cases/${caseId}/evidence?limit=${limit}&offset=${offset}`,
    ),
  get: (evidenceId: string) =>
    apiClient.get<ApiResponse<EvidenceRecord>>(`/evidence/${evidenceId}`),
  upload: (caseId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.postForm<ApiResponse<EvidenceRecord>>(
      `/cases/${caseId}/evidence`,
      formData,
    );
  },
};
