import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  DecisionLogEntry,
  DecisionSupportRun,
  ReviewQueueItem,
  WorkloadMetrics,
  WorkflowTask,
} from "../../types/decisionSupport";

export const decisionSupportApi = {
  generate: (caseId: string) =>
    apiClient.postJson<ApiResponse<DecisionSupportRun>>(
      `/cases/${caseId}/decision-support`,
      {},
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<DecisionSupportRun>>(
      `/cases/${caseId}/decision-support`,
    ),
  preview: (caseId: string) =>
    apiClient.get<ApiResponse<DecisionSupportRun>>(
      `/cases/${caseId}/decision-support/preview`,
    ),
  getRun: (runId: string) =>
    apiClient.get<ApiResponse<DecisionSupportRun>>(
      `/decision-support/${runId}`,
    ),
  listTasks: (caseId: string) =>
    apiClient.get<ApiResponse<{ items: WorkflowTask[]; total: number }>>(
      `/cases/${caseId}/decision-support/tasks`,
    ),
  updateTask: (taskId: string, body: { status?: string; priority?: string }) =>
    apiClient.patchJson<ApiResponse<WorkflowTask>>(
      `/decision-support/tasks/${taskId}`,
      body,
    ),
  listReviewQueue: (caseId: string) =>
    apiClient.get<ApiResponse<{ items: ReviewQueueItem[]; total: number }>>(
      `/cases/${caseId}/decision-support/review-queue`,
    ),
  listDecisions: (caseId: string) =>
    apiClient.get<ApiResponse<{ items: DecisionLogEntry[]; total: number }>>(
      `/cases/${caseId}/decision-support/decisions`,
    ),
  createDecision: (body: {
    case_id: string;
    decision_type: string;
    investigator: string;
    justification: string;
    task_id?: string;
  }) =>
    apiClient.postJson<ApiResponse<DecisionLogEntry>>(
      `/decision-support/decisions`,
      body,
    ),
  getMetrics: (caseId: string) =>
    apiClient.get<ApiResponse<WorkloadMetrics>>(
      `/cases/${caseId}/decision-support/metrics`,
    ),
};
