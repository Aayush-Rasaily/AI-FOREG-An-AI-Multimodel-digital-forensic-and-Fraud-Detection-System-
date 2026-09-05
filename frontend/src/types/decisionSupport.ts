export interface WorkloadMetrics {
  open_tasks: number;
  completed_tasks: number;
  pending_reviews: number;
  average_priority: number;
  critical_evidence_count: number;
  workflow_completion: number;
  investigation_progress: number;
  evidence_review_coverage: number;
}

export interface WorkflowTask {
  id?: string | null;
  run_id?: string | null;
  case_id?: string | null;
  task_key: string;
  task_type: string;
  stage: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  estimated_effort_hours: number;
  priority_score: number;
  required_evidence_ids: string[];
  supporting_intelligence: Record<string, unknown>;
  provenance: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ReviewQueueItem {
  id?: string | null;
  run_id?: string | null;
  case_id?: string | null;
  queue_key: string;
  evidence_id: string;
  priority: string;
  priority_score: number;
  reasons: string[];
  provenance: Record<string, unknown>;
}

export interface DecisionLogEntry {
  id: string;
  case_id: string;
  run_id?: string | null;
  task_id?: string | null;
  decision_type: string;
  investigator: string;
  justification: string;
  provenance: Record<string, unknown>;
  created_at: string;
}

export interface DecisionSupportRun {
  id?: string | null;
  case_id: string;
  status: string;
  current_stage: string;
  task_count: number;
  review_count: number;
  metrics: WorkloadMetrics;
  open_conflicts: Array<Record<string, unknown>>;
  provenance: Record<string, unknown>;
  engine_version: string;
  policy_version: string;
  created_at?: string | null;
  completed_at?: string | null;
  tasks: WorkflowTask[];
  review_queue: ReviewQueueItem[];
  persisted: boolean;
}
