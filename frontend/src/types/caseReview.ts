export interface ValidationMetrics {
  validation_pct: number;
  evidence_coverage_pct: number;
  review_completion_pct: number;
  approval_completion_pct: number;
  outstanding_issues: number;
  blocking_issues: number;
}

export interface ChecklistItem {
  id?: string | null;
  checklist_id?: string | null;
  run_id?: string | null;
  case_id?: string | null;
  item_key: string;
  item_code: string;
  title: string;
  status: string;
  suggested_status: string;
  blocking: boolean;
  outstanding: boolean;
  notes: string;
  reviewer?: string | null;
  reviewed_at?: string | null;
  provenance: Record<string, unknown>;
  created_at?: string | null;
}

export interface ReviewApproval {
  id?: string | null;
  run_id?: string | null;
  case_id?: string | null;
  checklist_id?: string | null;
  checklist_item_id?: string | null;
  reviewer: string;
  approver_role: string;
  decision: string;
  comments: string;
  provenance: Record<string, unknown>;
  created_at?: string | null;
}

export interface CaseReviewRun {
  id?: string | null;
  case_id: string;
  status: string;
  stage: string;
  checklist_count: number;
  approval_count: number;
  metrics: ValidationMetrics;
  outstanding: string[];
  blocking: string[];
  required_roles: string[];
  provenance: Record<string, unknown>;
  engine_version: string;
  policy_version: string;
  created_at?: string | null;
  completed_at?: string | null;
  checklist: ChecklistItem[];
  approvals: ReviewApproval[];
  persisted: boolean;
}

export interface CaseReviewHistoryItem {
  id: string;
  case_id: string;
  status: string;
  stage: string;
  checklist_count: number;
  approval_count: number;
  metrics: ValidationMetrics;
  engine_version: string;
  policy_version: string;
  created_at: string;
  completed_at?: string | null;
}
