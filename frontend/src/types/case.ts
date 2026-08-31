export type CaseStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "ON_HOLD"
  | "COMPLETED"
  | "ARCHIVED";

export type CasePriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface CaseRecord {
  id: string;
  case_number: string;
  title: string;
  description: string | null;
  status: CaseStatus;
  priority: CasePriority;
  created_at: string;
  updated_at: string;
}

export interface CaseListData {
  items: CaseRecord[];
  total: number;
  limit: number;
  offset: number;
}
