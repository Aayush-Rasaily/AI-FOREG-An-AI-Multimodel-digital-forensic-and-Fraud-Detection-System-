import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  InvestigationWorkflow,
  WorkflowListResponse,
  WorkflowMilestone,
  WorkflowNote,
  WorkflowNotification,
  WorkflowReview,
  WorkflowTask,
} from "../../types/workflow";

export const workflowApi = {
  getWorkflow(caseId: string) {
    return apiClient.get<ApiResponse<InvestigationWorkflow>>(
      `/cases/${caseId}/investigation-workflow`,
    );
  },

  updateStatus(
    caseId: string,
    payload: { status: string; assigned_analyst_id?: string | null },
  ) {
    return apiClient.patchJson<ApiResponse<InvestigationWorkflow>>(
      `/cases/${caseId}/investigation-workflow/status`,
      payload,
    );
  },

  listTasks(caseId: string) {
    return apiClient.get<ApiResponse<WorkflowListResponse<WorkflowTask>>>(
      `/cases/${caseId}/workflow-tasks`,
    );
  },

  createTask(
    caseId: string,
    payload: {
      title: string;
      task_type?: string;
      description?: string;
      assignee_id?: string;
    },
  ) {
    return apiClient.postJson<ApiResponse<WorkflowTask>>(
      `/cases/${caseId}/workflow-tasks`,
      payload,
    );
  },

  updateTask(
    taskId: string,
    payload: {
      title?: string;
      description?: string;
      assignee_id?: string;
      status?: string;
      action?: string;
    },
  ) {
    return apiClient.patchJson<ApiResponse<WorkflowTask>>(
      `/workflow-tasks/${taskId}`,
      payload,
    );
  },

  listNotes(caseId: string) {
    return apiClient.get<ApiResponse<WorkflowListResponse<WorkflowNote>>>(
      `/cases/${caseId}/workflow-notes`,
    );
  },

  createNote(
    caseId: string,
    payload: {
      content_markdown: string;
      category?: string;
      visibility?: string;
    },
  ) {
    return apiClient.postJson<ApiResponse<WorkflowNote>>(
      `/cases/${caseId}/workflow-notes`,
      payload,
    );
  },

  listReviews(caseId: string) {
    return apiClient.get<ApiResponse<WorkflowListResponse<WorkflowReview>>>(
      `/cases/${caseId}/workflow-reviews`,
    );
  },

  createReview(
    caseId: string,
    payload: {
      review_kind: string;
      status?: string;
      evidence_id?: string;
      report_id?: string;
      comments?: string;
      reason?: string;
    },
  ) {
    return apiClient.postJson<ApiResponse<WorkflowReview>>(
      `/cases/${caseId}/workflow-reviews`,
      payload,
    );
  },

  listMilestones(caseId: string) {
    return apiClient.get<ApiResponse<WorkflowListResponse<WorkflowMilestone>>>(
      `/cases/${caseId}/workflow-milestones`,
    );
  },

  listNotifications(caseId: string) {
    return apiClient.get<
      ApiResponse<WorkflowListResponse<WorkflowNotification>>
    >(`/cases/${caseId}/workflow-notifications`);
  },
};
