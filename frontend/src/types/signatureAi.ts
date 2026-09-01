export type SignatureVerdict =
  | "MATCH"
  | "NON_MATCH"
  | "INCONCLUSIVE"
  | "UNAVAILABLE";

export interface SignatureRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  page_number: number | null;
  confidence: number | null;
}

export interface SignatureVerificationRun {
  id: string;
  reference_hash: string;
  questioned_hash: string;
  model: string;
  model_version: string;
  similarity: number | null;
  threshold: number;
  verdict: SignatureVerdict;
  device: string;
  processing_time_ms: number | null;
  reference_evidence_id: string | null;
  questioned_evidence_id: string | null;
  localization: SignatureRegion | null;
  artifact_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface SignatureVerificationListData {
  items: SignatureVerificationRun[];
  total: number;
  limit: number;
  offset: number;
}
