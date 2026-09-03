export type CorrelationRunStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED";

export type CorrelationType =
  | "same_hash"
  | "same_email"
  | "same_phone"
  | "same_device"
  | "same_camera"
  | "same_signature"
  | "same_logo"
  | "same_qr"
  | "same_audio_speaker"
  | "same_location"
  | "same_document"
  | "similar_filename"
  | "temporal_overlap"
  | "shared_metadata"
  | "shared_identifier";

export interface CorrelationSupport {
  id: string;
  support_kind: string;
  support_ref: string;
  label: string;
  value: string | null;
  metadata: Record<string, unknown>;
}

export interface EvidenceCorrelation {
  id: string;
  analysis_run_id: string;
  case_id: string;
  left_evidence_id: string;
  right_evidence_id: string;
  correlation_id: string;
  correlation_type: CorrelationType;
  score: number;
  confidence: number;
  explanation: string;
  supporting_findings: string[];
  supporting_metadata: Record<string, unknown>;
  supporting_entities: string[];
  provenance: Record<string, unknown>;
  supports: CorrelationSupport[];
  created_at: string;
}

export interface CorrelationRun {
  id: string;
  case_id: string;
  status: CorrelationRunStatus;
  engine_version: string;
  policy_version: string;
  correlation_count: number;
  evidence_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface CorrelationDetail extends CorrelationRun {
  correlations: EvidenceCorrelation[];
}

export interface CorrelationRunListData {
  items: CorrelationRun[];
  total: number;
  limit: number;
  offset: number;
}
