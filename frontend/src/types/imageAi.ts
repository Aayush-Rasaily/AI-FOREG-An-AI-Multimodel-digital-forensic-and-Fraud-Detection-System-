export type ImageFindingCategory =
  | "AI_GENERATED"
  | "DEEPFAKE"
  | "MANIPULATION"
  | "LOGO"
  | "ID_DOCUMENT"
  | "IMAGE";

export type ImageAnalysisStatus = "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED";

export interface ImageFindingRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  page_number: number | null;
  frame_number: number | null;
  polygon: [number, number][] | null;
  normalized_location: Record<string, number> | null;
}

export interface ImageAIFinding {
  id: string;
  analysis_run_id: string;
  detector: string;
  category: ImageFindingCategory;
  severity: string;
  confidence: number;
  description: string;
  explanation: string;
  recommendation: string | null;
  model_name: string;
  model_version: string;
  model_framework: string;
  heatmap_artifact_id: string | null;
  mask_artifact_id: string | null;
  regions: ImageFindingRegion[];
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ImageAnalysisRun {
  id: string;
  evidence_id: string;
  status: ImageAnalysisStatus;
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

export interface ImageAnalysisRunListData {
  items: ImageAnalysisRun[];
  total: number;
  limit: number;
  offset: number;
}

export interface ImageAIFindingListData {
  items: ImageAIFinding[];
  total: number;
  limit: number;
  offset: number;
}
