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

export type ProcessingJobStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"
  | "CANCELLED";

export type ProcessingJobType =
  | "INGESTION_INSPECTION"
  | "METADATA_EXTRACTION"
  | "PREVIEW_GENERATION"
  | "FILE_CLASSIFICATION"
  | "PREPROCESSING";

export interface ProcessingJob {
  id: string;
  evidence_id: string;
  job_type: ProcessingJobType;
  status: ProcessingJobStatus;
  priority: number;
  attempt: number;
  max_attempts: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
}

export interface ProcessingJobListData {
  items: ProcessingJob[];
  total: number;
  limit: number;
  offset: number;
}

export type ArtifactType =
  | "PREVIEW"
  | "THUMBNAIL"
  | "METADATA"
  | "CLASSIFICATION"
  | "DERIVATIVE";

export interface EvidenceArtifact {
  id: string;
  evidence_id: string;
  artifact_type: ArtifactType;
  mime_type: string;
  file_size: number;
  sha256_hash: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

export interface ArtifactListData {
  items: EvidenceArtifact[];
  total: number;
  limit: number;
  offset: number;
}

export type ExtractionStatus =
  | "SUCCEEDED"
  | "PARTIAL"
  | "UNAVAILABLE"
  | "FAILED";

export type ExtractionType =
  | "TEXT"
  | "WORD"
  | "LINE"
  | "IMAGE_REGION"
  | "FACE_REGION"
  | "SIGNATURE_REGION"
  | "LOGO_REGION"
  | "STAMP_REGION"
  | "NUMBER"
  | "DATE"
  | "QR_CODE"
  | "BARCODE"
  | "TABLE"
  | "PAGE"
  | "FRAME"
  | "AUDIO_STREAM"
  | "METADATA";

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ExtractionRecord {
  id: string;
  evidence_id: string;
  artifact_id: string | null;
  extraction_type: ExtractionType;
  source_type: "ORIGINAL" | "ARTIFACT";
  source_identifier: string;
  page_number: number | null;
  frame_number: number | null;
  timestamp_ms: number | null;
  content: string | null;
  confidence: number | null;
  location: BoundingBox | null;
  normalized_location: BoundingBox | null;
  method: string;
  version: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ExtractionListData {
  status: ExtractionStatus;
  error_code: string | null;
  items: ExtractionRecord[];
  total: number;
  limit: number;
  offset: number;
}
