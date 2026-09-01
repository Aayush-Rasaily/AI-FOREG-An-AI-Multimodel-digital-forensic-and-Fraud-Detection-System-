export type ComparisonRunStatus = "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED";

export type DifferenceType =
  | "TEXT_CHANGED"
  | "TEXT_INSERTED"
  | "TEXT_REMOVED"
  | "NUMBER_CHANGED"
  | "DATE_CHANGED"
  | "IMAGE_CHANGED"
  | "LOGO_CHANGED"
  | "LAYOUT_CHANGED"
  | "METADATA_CHANGED"
  | "PAGE_INSERTED"
  | "PAGE_REMOVED"
  | "SIGNATURE_CHANGED"
  | "UNKNOWN";

export type DifferenceSeverity =
  | "INFO"
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

export interface ReferenceEvidence {
  id: string;
  case_id: string;
  evidence_id: string;
  label: string;
  description: string | null;
  reference_hash: string;
  original_filename: string;
  mime_type: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ReferenceEvidenceListData {
  items: ReferenceEvidence[];
  total: number;
  limit: number;
  offset: number;
}

export interface DifferenceRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  page_number: number | null;
  frame_number: number | null;
  polygon: [number, number][] | null;
  normalized_location: Record<string, number> | null;
}

export interface Difference {
  id: string;
  comparison_run_id: string;
  matcher: string;
  difference_type: DifferenceType;
  severity: DifferenceSeverity;
  confidence: number;
  description: string;
  explanation: string;
  original_value: string | null;
  submitted_value: string | null;
  regions: DifferenceRegion[];
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface DifferenceListData {
  items: Difference[];
  total: number;
  limit: number;
  offset: number;
}

export interface ComparisonRun {
  id: string;
  evidence_id: string;
  reference_evidence_id: string;
  reference_record_id: string;
  status: ComparisonRunStatus;
  engine_version: string;
  differences_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
}

export interface ComparisonRunListData {
  items: ComparisonRun[];
  total: number;
  limit: number;
  offset: number;
}

export interface ComparisonSummary {
  status: ComparisonRunStatus;
  comparison_run_id: string | null;
  differences_count: number;
  type_counts: Record<string, number>;
  error_code?: string | null;
}
