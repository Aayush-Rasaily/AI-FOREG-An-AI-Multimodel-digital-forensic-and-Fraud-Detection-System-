export type TimelineRunStatus = "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED";

export type TimelineEventType =
  | "evidence_uploaded"
  | "evidence_updated"
  | "processing_queued"
  | "processing_started"
  | "processing_completed"
  | "extraction_completed"
  | "custody_event"
  | "forensic_analysis_completed"
  | "image_ai_completed"
  | "document_ai_completed"
  | "signature_ai_completed"
  | "video_ai_completed"
  | "audio_ai_completed"
  | "fusion_completed"
  | "case_intelligence_completed"
  | "report_generated"
  | "metadata_timestamp"
  | "timestamp_missing";

export type TimelineConflictType =
  | "multiple_timestamps"
  | "filesystem_before_exif"
  | "future_timestamp"
  | "clock_drift"
  | "timezone_mismatch"
  | "duplicate_event";

export interface TimelineEvent {
  id: string;
  timeline_id: string;
  case_id: string;
  evidence_id: string | null;
  event_id: string;
  event_type: TimelineEventType;
  timestamp: string | null;
  timezone: string | null;
  normalized_timestamp: string | null;
  confidence: number;
  uncertainty_ms: number;
  description: string;
  source: string;
  source_id: string;
  provenance: Record<string, unknown>;
  metadata: Record<string, unknown>;
  supporting_artifacts: string[];
  created_at: string;
}

export interface TimelineConflict {
  id: string;
  timeline_id: string;
  case_id: string;
  conflict_id: string;
  conflict_type: TimelineConflictType;
  evidence_id: string | null;
  involved_event_ids: string[];
  explanation: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface TimelineRun {
  id: string;
  case_id: string;
  status: TimelineRunStatus;
  engine_version: string;
  policy_version: string;
  event_count: number;
  conflicts_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface TimelineDetail extends TimelineRun {
  events: TimelineEvent[];
  conflicts: TimelineConflict[];
}

export interface TimelineRunListData {
  items: TimelineRun[];
  total: number;
  limit: number;
  offset: number;
}
