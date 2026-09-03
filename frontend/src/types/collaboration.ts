export interface CaseMember {
  id: string;
  case_id: string;
  user_id: string;
  username: string | null;
  display_name: string | null;
  role: string;
  invited_by: string | null;
  created_at: string;
}

export interface CaseMemberList {
  items: CaseMember[];
  total: number;
}

export interface CollaborationTask {
  id: string;
  case_id: string;
  title: string;
  description: string | null;
  assignee_id: string | null;
  created_by: string;
  priority: string;
  status: string;
  due_date: string | null;
  linked_evidence_id: string | null;
  linked_report_id: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskList {
  items: CollaborationTask[];
  total: number;
}

export interface CollaborationComment {
  id: string;
  case_id: string;
  author_id: string;
  author_username: string | null;
  resource_type: string;
  resource_id: string;
  parent_id: string | null;
  body: string;
  body_markdown: boolean;
  edit_history: Array<Record<string, unknown>>;
  is_deleted: boolean;
  mentions: string[];
  created_at: string;
  updated_at: string;
}

export interface CommentList {
  items: CollaborationComment[];
  total: number;
}

export interface ActivityItem {
  id: string;
  case_id: string;
  actor_id: string | null;
  actor_username: string;
  action: string;
  summary: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface ActivityList {
  items: ActivityItem[];
  total: number;
}

export interface WorkflowState {
  case_id: string;
  stage: string;
  version: number;
  updated_by: string | null;
  updated_at: string;
  allowed_transitions: string[];
}

export interface NotificationItem {
  id: string;
  user_id: string;
  case_id: string | null;
  kind: string;
  title: string;
  body: string;
  status: string;
  payload: Record<string, unknown>;
  created_at: string;
  read_at: string | null;
}

export interface NotificationList {
  items: NotificationItem[];
  total: number;
  unread_count: number;
}

export interface ReviewItem {
  id: string;
  case_id: string;
  resource_type: string;
  resource_id: string;
  state: string;
  requested_by: string;
  reviewer_id: string | null;
  decision: string | null;
  comments: string | null;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface EvidenceAssignment {
  id: string;
  case_id: string;
  evidence_id: string;
  assignee_id: string;
  assigned_by: string;
  priority: string;
  status: string;
  due_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}
