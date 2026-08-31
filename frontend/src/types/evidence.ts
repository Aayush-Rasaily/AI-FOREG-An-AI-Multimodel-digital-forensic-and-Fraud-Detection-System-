export type EvidenceStatus =
  | "REGISTERED"
  | "READY_FOR_ANALYSIS"
  | "ANALYZING"
  | "ANALYZED"
  | "FAILED"
  | "QUARANTINED";

export interface CustodyEvent {
  id: string;
  evidence_id: string;
  event_type: string;
  timestamp: string;
  actor_type: string;
  actor_id: string | null;
  description: string;
  sha256_hash: string;
  metadata: Record<string, unknown>;
}

export interface EvidenceRecord {
  id: string;
  case_id: string;
  evidence_number: string;
  original_filename: string;
  stored_filename: string;
  mime_type: string;
  file_size: number;
  sha256_hash: string;
  status: EvidenceStatus;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  custody_events: CustodyEvent[];
}

export interface EvidenceListData {
  items: EvidenceRecord[];
  total: number;
}
