export type AIModelStatus = "REGISTERED" | "LOADED" | "UNLOADED" | "FAILED";

export interface AIModel {
  id: string;
  name: string;
  version: string;
  framework: string;
  author: string;
  license: string;
  input_type: string;
  output_type: string;
  model_hash: string;
  required_device: string;
  status: AIModelStatus;
  current_device: string | null;
  last_loaded_at: string | null;
  last_latency_ms: number | null;
  supported_tasks: string[];
  cache_state: Record<string, unknown> | null;
  health: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AIModelListData {
  items: AIModel[];
  total: number;
  limit: number;
  offset: number;
  cache_statistics: Record<string, number>;
  devices: Array<Record<string, unknown>>;
}

export interface InferenceLog {
  id: string;
  level: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface InferenceJob {
  id: string;
  model_record_id: string;
  model_name: string;
  model_version: string;
  task: string;
  device: string;
  status: string;
  latency_ms: number | null;
  batch_size: number;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  logs: InferenceLog[];
}

export interface InferenceJobListData {
  items: InferenceJob[];
  total: number;
  limit: number;
  offset: number;
}
