import type { ApiResponse } from "../../types/api";
import type {
  CaseListData,
  CasePriority,
  CaseRecord,
  CaseStatus,
} from "../../types/case";
import { apiClient } from "./client";

export interface CreateCaseInput {
  title: string;
  description?: string;
  priority: CasePriority;
}

export interface UpdateCaseInput {
  title?: string;
  description?: string | null;
  status?: CaseStatus;
  priority?: CasePriority;
}

export const caseService = {
  list: (limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<CaseListData>>(
      `/cases?limit=${limit}&offset=${offset}`,
    ),
  get: (caseId: string) =>
    apiClient.get<ApiResponse<CaseRecord>>(`/cases/${caseId}`),
  create: (input: CreateCaseInput) =>
    apiClient.postJson<ApiResponse<CaseRecord>>("/cases", input),
  update: (caseId: string, input: UpdateCaseInput) =>
    apiClient.patchJson<ApiResponse<CaseRecord>>(`/cases/${caseId}`, input),
};
