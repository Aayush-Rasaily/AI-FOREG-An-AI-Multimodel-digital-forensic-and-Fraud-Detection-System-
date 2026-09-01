export type VideoFindingCategory =
  | "DEEPFAKE"
  | "SYNTHETIC_VIDEO"
  | "FRAME_MANIPULATION"
  | "TEMPORAL_INCONSISTENCY"
  | "FACE_MANIPULATION"
  | "FACE_INCONSISTENCY"
  | "COMPRESSION"
  | "METADATA"
  | "CAPABILITY"
  | "VIDEO";

export type VideoAnalysisStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"
  | "UNAVAILABLE"
  | "CANCELLED";

export type DetectionMethod = "classical" | "ai";

export interface TemporalEvidence {
  start_frame: number | null;
  end_frame: number | null;
  start_timestamp_ms: number | null;
  end_timestamp_ms: number | null;
  evidence_type?: string;
}

export interface VideoFindingRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  frame_number: number | null;
  timestamp_ms: number | null;
  polygon: [number, number][] | null;
  normalized_location: Record<string, number> | null;
}

export interface VideoAIFinding {
  id: string;
  analysis_run_id: string;
  detector: string;
  category: VideoFindingCategory;
  severity: string;
  confidence: number | null;
  method: DetectionMethod;
  description: string;
  explanation: string;
  recommendation: string | null;
  model_name: string;
  model_version: string;
  model_framework: string;
  temporal: TemporalEvidence | null;
  artifact_id: string | null;
  regions: VideoFindingRegion[];
  metadata: Record<string, unknown>;
  limitations: string | null;
  created_at: string;
}

export interface VideoFrame {
  frame_index: number;
  frame_number: number;
  timestamp_ms: number;
  timestamp_seconds: number;
  frame_id: string;
  artifact_id: string | null;
  width: number | null;
  height: number | null;
}

export interface VideoTimelineEntry {
  detector: string;
  category: string;
  severity: string;
  confidence: number | null;
  method: string;
  start_frame: number | null;
  end_frame: number | null;
  start_timestamp_ms: number | null;
  end_timestamp_ms: number | null;
  description: string;
}

export interface VideoAnalysisRun {
  id: string;
  evidence_id: string;
  status: VideoAnalysisStatus;
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
  video?: Record<string, unknown> | null;
}

export interface VideoAnalysisDetail extends VideoAnalysisRun {
  timeline: VideoTimelineEntry[];
  frames: VideoFrame[];
  artifacts: Record<string, unknown>[];
}

export interface VideoAnalysisRunListData {
  items: VideoAnalysisRun[];
  total: number;
  limit: number;
  offset: number;
}

export interface VideoAIFindingListData {
  items: VideoAIFinding[];
  total: number;
  limit: number;
  offset: number;
}
