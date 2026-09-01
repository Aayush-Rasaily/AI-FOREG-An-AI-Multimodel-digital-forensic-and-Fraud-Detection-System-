export type DocumentFindingCategory =
  | "TAMPERING"
  | "TEXT_INCONSISTENCY"
  | "FONT_INCONSISTENCY"
  | "LAYOUT_INCONSISTENCY"
  | "LOGO"
  | "METADATA"
  | "REGION_ANOMALY"
  | "DATE_INCONSISTENCY"
  | "NUMBER_INCONSISTENCY"
  | "REFERENCE_MISMATCH"
  | "SIGNATURE"
  | "ID_DOCUMENT"
  | "CAPABILITY";

export type DocumentAnalysisStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED";

export type DetectionMethod = "classical" | "ai" | "reference";

export interface DocumentFindingRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  page_number: number | null;
  frame_number: number | null;
  polygon: [number, number][] | null;
  normalized_location: Record<string, number> | null;
}

export interface DocumentAIFinding {
  id: string;
  analysis_run_id: string;
  detector: string;
  category: DocumentFindingCategory;
  severity: string;
  method: DetectionMethod;
  confidence: number | null;
  description: string;
  explanation: string;
  recommendation: string | null;
  model_name: string;
  model_version: string;
  model_framework: string;
  artifact_id: string | null;
  regions: DocumentFindingRegion[];
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface DocumentAnalysisRun {
  id: string;
  evidence_id: string;
  status: DocumentAnalysisStatus;
  engine_version: string;
  device: string;
  latency_ms: number | null;
  findings_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
}

export interface DocumentAnalysisRunListData {
  items: DocumentAnalysisRun[];
  total: number;
  limit: number;
  offset: number;
}

export interface DocumentAIFindingListData {
  items: DocumentAIFinding[];
  total: number;
  limit: number;
  offset: number;
}
