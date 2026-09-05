import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  CaseReviewHistoryItem,
  CaseReviewRun,
  ChecklistItem,
  ReviewApproval,
  ValidationMetrics,
} from "../../types/caseReview";

export const caseReviewApi = {
  generate: (caseId: string) =>
    apiClient.postJson<ApiResponse<CaseReviewRun>>(
      `/cases/${caseId}/case-review`,
      {},
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<CaseReviewRun>>(
      `/cases/${caseId}/case-review`,
    ),
  preview: (caseId: string) =>
    apiClient.get<ApiResponse<CaseReviewRun>>(
      `/cases/${caseId}/case-review/preview`,
    ),
  getRun: (reviewId: string) =>
    apiClient.get<ApiResponse<CaseReviewRun>>(
      `/case-review/${reviewId}`,
    ),
  listChecklist: (caseId: string) =>
    apiClient.get<ApiResponse<{ items: ChecklistItem[]; total: number }>>(
      `/cases/${caseId}/case-review/checklist`,
    ),
  updateChecklistItem: (
    itemId: string,
    body: { status?: string; notes?: string; reviewer?: string },
  ) =>
    apiClient.patchJson<ApiResponse<ChecklistItem>>(
      `/case-review/checklist/${itemId}`,
      body,
    ),
  listApprovals: (caseId: string) =>
    apiClient.get<ApiResponse<{ items: ReviewApproval[]; total: number }>>(
      `/cases/${caseId}/case-review/approvals`,
    ),
  createApproval: (body: {
    case_id: string;
    run_id?: string;
    reviewer: string;
    approver_role: string;
    decision: string;
    comments?: string;
  }) =>
    apiClient.postJson<ApiResponse<ReviewApproval>>(
      `/case-review/approvals`,
      body,
    ),
  getMetrics: (caseId: string) =>
    apiClient.get<ApiResponse<ValidationMetrics>>(
      `/cases/${caseId}/case-review/metrics`,
    ),
  getHistory: (caseId: string) =>
    apiClient.get<
      ApiResponse<{ items: CaseReviewHistoryItem[]; total: number }>
    >(`/cases/${caseId}/case-review/history`),
};
