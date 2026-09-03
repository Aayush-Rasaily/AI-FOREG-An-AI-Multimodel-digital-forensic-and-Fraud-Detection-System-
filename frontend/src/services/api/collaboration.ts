import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  ActivityList,
  CaseMember,
  CaseMemberList,
  CollaborationComment,
  CollaborationTask,
  CommentList,
  EvidenceAssignment,
  NotificationList,
  ReviewItem,
  TaskList,
  WorkflowState,
} from "../../types/collaboration";

export const collaborationApi = {
  listMembers(caseId: string) {
    return apiClient.get<ApiResponse<CaseMemberList>>(
      `/cases/${caseId}/members`,
    );
  },
  addMember(caseId: string, userId: string, role: string) {
    return apiClient.postJson<ApiResponse<CaseMember>>(
      `/cases/${caseId}/members`,
      { user_id: userId, role },
    );
  },
  updateMember(
    caseId: string,
    memberId: string,
    payload: { role?: string; transfer_ownership?: boolean },
  ) {
    return apiClient.patchJson<ApiResponse<CaseMember>>(
      `/cases/${caseId}/members/${memberId}`,
      payload,
    );
  },
  removeMember(caseId: string, memberId: string) {
    return apiClient.deleteJson<ApiResponse<{ removed: boolean }>>(
      `/cases/${caseId}/members/${memberId}`,
    );
  },
  listTasks(caseId: string) {
    return apiClient.get<ApiResponse<TaskList>>(`/cases/${caseId}/tasks`);
  },
  createTask(
    caseId: string,
    payload: {
      title: string;
      description?: string;
      assignee_id?: string;
      priority?: string;
      due_date?: string;
    },
  ) {
    return apiClient.postJson<ApiResponse<CollaborationTask>>(
      `/cases/${caseId}/tasks`,
      payload,
    );
  },
  updateTask(taskId: string, payload: Record<string, unknown>) {
    return apiClient.patchJson<ApiResponse<CollaborationTask>>(
      `/tasks/${taskId}`,
      payload,
    );
  },
  listComments(resourceType: string, resourceId: string) {
    return apiClient.get<ApiResponse<CommentList>>(
      `/comments/${resourceType}/${resourceId}`,
    );
  },
  createComment(payload: {
    case_id: string;
    resource_type: string;
    resource_id: string;
    body: string;
    parent_id?: string;
  }) {
    return apiClient.postJson<ApiResponse<CollaborationComment>>(
      "/comments",
      payload,
    );
  },
  listActivity(caseId: string) {
    return apiClient.get<ApiResponse<ActivityList>>(
      `/cases/${caseId}/activity`,
    );
  },
  getWorkflow(caseId: string) {
    return apiClient.get<ApiResponse<WorkflowState>>(
      `/cases/${caseId}/workflow`,
    );
  },
  updateWorkflow(caseId: string, stage: string) {
    return apiClient.patchJson<ApiResponse<WorkflowState>>(
      `/cases/${caseId}/workflow`,
      { stage },
    );
  },
  listNotifications() {
    return apiClient.get<ApiResponse<NotificationList>>("/notifications");
  },
  updateNotification(id: string, status: string) {
    return apiClient.patchJson<ApiResponse<NotificationItemLike>>(
      `/notifications/${id}`,
      { status },
    );
  },
  createReview(payload: {
    case_id: string;
    resource_type: string;
    resource_id: string;
    reviewer_id?: string;
    comments?: string;
  }) {
    return apiClient.postJson<ApiResponse<ReviewItem>>("/reviews", payload);
  },
  decideReview(reviewId: string, decision: string, comments?: string) {
    return apiClient.patchJson<ApiResponse<ReviewItem>>(
      `/reviews/${reviewId}`,
      { decision, comments },
    );
  },
  assignEvidence(
    evidenceId: string,
    payload: { assignee_id: string; priority?: string; notes?: string },
  ) {
    return apiClient.postJson<ApiResponse<EvidenceAssignment>>(
      `/evidence/${evidenceId}/assign`,
      payload,
    );
  },
  listAssignments(evidenceId: string) {
    return apiClient.get<ApiResponse<EvidenceAssignmentList>>(
      `/evidence/${evidenceId}/assignments`,
    );
  },
};

interface EvidenceAssignmentList {
  items: EvidenceAssignment[];
  total: number;
}

interface NotificationItemLike {
  id: string;
  status: string;
}
