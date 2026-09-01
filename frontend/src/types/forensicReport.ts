export type ReportStatus = "QUEUED" | "GENERATING" | "COMPLETED" | "FAILED";

export interface ForensicReport {
  id: string;
  case_id: string;
  status: ReportStatus;
  report_version: string;
  engine_version: string;
  fusion_policy_version: string | null;
  case_intelligence_policy_version: string | null;
  case_intelligence_run_id: string | null;
  evidence_count: number;
  evidence_hashes: string[];
  pdf_sha256: string | null;
  has_pdf: boolean;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface ForensicReportDetail extends ForensicReport {
  content: Record<string, unknown>;
  executive_summary: Record<string, unknown>;
  explainability: Record<string, unknown>;
}

export interface ForensicReportListData {
  items: ForensicReport[];
  total: number;
  limit: number;
  offset: number;
}

export interface ForensicReportStatus {
  id: string;
  status: ReportStatus;
  error_code: string | null;
  error_message: string | null;
  completed_at: string | null;
}
