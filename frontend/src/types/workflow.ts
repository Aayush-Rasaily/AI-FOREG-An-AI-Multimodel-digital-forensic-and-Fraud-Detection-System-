export type InvestigationStatus =
  | "NEW"
  | "ACTIVE"
  | "UNDER_REVIEW"
  | "REQUIRES_CHANGES"
  | "APPROVED"
  | "REPORTED"
  | "ARCHIVED";

export type WorkflowTaskType =
  | "AI_ANALYSIS"
  | "FORENSIC_REVIEW"
  | "REPORT_REVIEW"
  | "EVIDENCE_VALIDATION"
  | "TIMELINE_REVIEW"
  | "CORRELATION_REVIEW"
  | "FUSION_REVIEW"
  | "GENERAL";

export type WorkflowTaskStatus =
  | "OPEN"
  | "ASSIGNED"
  | "COMPLETED"
  | "REOPENED"
  | "CANCELLED";

export interface WorkflowActivityEvent {
  action: string;
  summary: string;
  actor_id: string | null;
  actor_username: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

export interface InvestigationWorkflow {
  id: string;
  case_id: string;
  status: InvestigationStatus;
  assigned_analyst_id: string | null;
  allowed_transitions: InvestigationStatus[];
  activity: WorkflowActivityEvent[];
  policy_version: string;
  engine_version: string;
  created_at: string;
  updated_at: string;
  status_changed_at: string | null;
  status_changed_by: string | null;
}

export interface WorkflowTask {
  id: string;
  workflow_id: string;
  case_id: string;
  task_type: WorkflowTaskType | string;
  title: string;
  description: string | null;
  status: WorkflowTaskStatus | string;
  assignee_id: string | null;
  created_by: string | null;
  linked_evidence_id: string | null;
  linked_report_id: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowNote {
  id: string;
  workflow_id: string;
  case_id: string;
  category: string;
  visibility: string;
  content_markdown: string;
  author_id: string | null;
  history: Array<Record<string, unknown>>;
  created_at: string;
  updated_at: string;
}

export interface WorkflowReview {
  id: string;
  workflow_id: string;
  case_id: string;
  review_kind: "evidence" | "report" | string;
  status: string;
  evidence_id: string | null;
  report_id: string | null;
  reviewer_id: string | null;
  comments: string | null;
  reason: string | null;
  decided_at: string | null;
  history: Array<Record<string, unknown>>;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowMilestone {
  id: string;
  workflow_id: string;
  case_id: string;
  milestone_type: string;
  label: string;
  reached_at: string;
  reached_by: string | null;
  auto_derived: boolean;
  details: Record<string, unknown>;
  created_at: string;
}

export interface WorkflowNotification {
  id: string;
  workflow_id: string;
  case_id: string;
  user_id: string;
  kind: string;
  title: string;
  body: string;
  status: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface WorkflowListResponse<T> {
  items: T[];
  total: number;
}
