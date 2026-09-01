export type AudioFindingCategory =
  | "SYNTHETIC_AUDIO"
  | "VOICE_CLONE"
  | "DEEPFAKE_VOICE"
  | "SPEAKER_INCONSISTENCY"
  | "REFERENCE_MISMATCH"
  | "SPLICING"
  | "WAVEFORM"
  | "SPECTRAL"
  | "COMPRESSION"
  | "NOISE"
  | "SILENCE"
  | "METADATA"
  | "CAPABILITY"
  | "AUDIO";

export type AudioAnalysisStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"
  | "UNAVAILABLE"
  | "CANCELLED";

export type DetectionMethod = "classical" | "ai" | "reference";

export interface TemporalEvidence {
  start_time_ms: number | null;
  end_time_ms: number | null;
  duration_ms: number | null;
  evidence_type?: string;
}

export interface AudioFindingRegion {
  segment_id: string | null;
  start_time_ms: number | null;
  end_time_ms: number | null;
  duration_ms: number | null;
  metrics: Record<string, unknown> | null;
}

export interface AudioAIFinding {
  id: string;
  analysis_run_id: string;
  detector: string;
  category: AudioFindingCategory;
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
  regions: AudioFindingRegion[];
  metadata: Record<string, unknown>;
  limitations: string | null;
  created_at: string;
}

export interface AudioTimelineEntry {
  detector: string;
  category: string;
  severity: string;
  confidence: number | null;
  method: string;
  start_time_ms: number | null;
  end_time_ms: number | null;
  duration_ms: number | null;
  description: string;
}

export interface AudioSegment {
  segment_id: string;
  detector: string;
  category: string;
  severity: string;
  confidence: number | null;
  start_time_ms: number | null;
  end_time_ms: number | null;
  duration_ms: number | null;
  description: string;
}

export interface AudioFeatureSummary {
  sample_rate: number;
  duration_seconds: number;
  channels: number;
  rms_energy: number;
  zero_crossing_rate: number;
  spectral_centroid_hz: number;
  mfcc_mean: number[];
  window_count: number;
}

export interface AudioAnalysisRun {
  id: string;
  evidence_id: string;
  reference_evidence_id: string | null;
  status: AudioAnalysisStatus;
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
  audio?: Record<string, unknown> | null;
}

export interface AudioAnalysisDetail extends AudioAnalysisRun {
  timeline: AudioTimelineEntry[];
  segments: AudioSegment[];
  features: AudioFeatureSummary | null;
  artifacts: Record<string, unknown>[];
}

export interface AudioAnalysisRunListData {
  items: AudioAnalysisRun[];
  total: number;
  limit: number;
  offset: number;
}

export interface AudioAIFindingListData {
  items: AudioAIFinding[];
  total: number;
  limit: number;
  offset: number;
}

export interface AudioAnalysisRequest {
  reference_evidence_id?: string | null;
}
