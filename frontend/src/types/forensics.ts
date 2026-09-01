export type ForensicSeverity =
  | "INFO"
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

export type FindingCategory =
  | "IMAGE"
  | "DOCUMENT"
  | "METADATA"
  | "COMPRESSION"
  | "COPY_MOVE"
  | "SPLICING"
  | "LAYOUT"
  | "FONT"
  | "OVERLAY"
  | "NOISE"
  | "EDGE"
  | "DATE"
  | "NUMBER"
  | "OTHER";

export type AnalysisRunStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED";

export interface FindingRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  page_number: number | null;
  frame_number: number | null;
  polygon: [number, number][] | null;
  normalized_location: {
    x: number;
    y: number;
    width: number;
    height: number;
  } | null;
}

export interface ForensicFinding {
  id: string;
  analysis_run_id: string;
  detector: string;
  category: FindingCategory;
  severity: ForensicSeverity;
  confidence: number;
  description: string;
  explanation: string;
  recommendation: string | null;
  regions: FindingRegion[];
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface FindingListData {
  items: ForensicFinding[];
  total: number;
  limit: number;
  offset: number;
}

export interface AnalysisRun {
  id: string;
  evidence_id: string;
  status: AnalysisRunStatus;
  engine_version: string;
  findings_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
}

export interface AnalysisRunListData {
  items: AnalysisRun[];
  total: number;
  limit: number;
  offset: number;
}

export interface AnalysisSummary {
  status: AnalysisRunStatus;
  analysis_run_id: string | null;
  findings_count: number;
  severity_counts: Record<string, number>;
  error_code?: string | null;
}
