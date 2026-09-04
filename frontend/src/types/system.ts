export interface HealthSnapshot {
  status: string;
  timestamp: string;
  service: string;
  version: string;
  environment: string;
  uptime_seconds: number;
  python_version: string;
  platform: string;
  database: { status: string };
  redis: { status: string; detail: string };
  resources: {
    cpu_percent: number | null;
    memory_mb: number | null;
    disk_percent: number | null;
    gpu_available: boolean;
  };
  engine_version: string;
  policy_version: string;
}

export interface SystemMetrics {
  evidence_count: number;
  case_count: number;
  report_count: number;
  timeline_count: number;
  fusion_run_count: number;
  entity_graph_count: number;
  correlation_count: number;
  ai_analysis_count: number;
  processing_job_count: number;
  average_processing_time_ms: number | null;
  failure_rate: number;
  storage_growth_bytes: number | null;
}

export interface JobCategoryCounts {
  queued: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
}

export interface JobsSummary {
  categories: Record<string, JobCategoryCounts>;
  totals: JobCategoryCounts;
  active_analyses: number;
  queue_length: number;
  category_list: string[];
}

export interface StorageStats {
  backend: string;
  root_configured: boolean;
  used_bytes: number;
  used_mb: number;
  disk_total_bytes: number | null;
  disk_free_bytes: number | null;
  disk_percent: number | null;
  max_upload_size_mb: number;
}

export interface DiagnosticCheck {
  name: string;
  status: string;
  detail: string;
}

export interface DiagnosticsResult {
  overall_status: string;
  checks: DiagnosticCheck[];
  check_names: string[];
  pass_count: number;
  warn_count: number;
  fail_count: number;
}

export interface DiagnosticsRun extends DiagnosticsResult {
  id: string;
  results_json: DiagnosticsResult;
  engine_version: string;
  policy_version: string;
  created_at: string;
}

/** Phase 8G deployment / release types (additive). */

export interface SystemCheckItem {
  check: string;
  status: string;
  message: string;
  free_bytes?: string | null;
  total_bytes?: string | null;
}

export interface SystemVersionInfo {
  application_version: string;
  service: string;
  environment: string;
  policy_version: string;
  engine_version: string;
}

export interface SystemReleaseInfo {
  application_version: string;
  schema_version: string;
  migration_version: string;
  environment: string;
  policy_versions: Record<string, string>;
  ai_engine_versions: Record<string, string>;
  build_metadata: Record<string, unknown>;
  git_commit: string | null;
}

export interface SystemLiveness {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  policy_version: string;
  engine_version: string;
}

export interface SystemReadiness {
  status: string;
  ready: boolean;
  validation_status: string;
  checks: SystemCheckItem[];
  timestamp: string;
  policy_version: string;
  engine_version: string;
}

export interface SystemStartupValidation {
  status: string;
  checks: SystemCheckItem[];
  fail_count: number;
  timestamp: string;
  environment: string;
  version: string;
  policy_version: string;
  engine_version: string;
  graceful_shutdown_supported: boolean;
}

export interface SystemConfiguration {
  profile: Record<string, unknown>;
  export: Record<string, unknown>;
  findings: SystemCheckItem[];
}

export interface SystemValidationResult {
  status: string;
  checks: SystemCheckItem[];
  fail_count: number;
  warn_count: number;
  pass_count: number;
  policy_version: string;
  engine_version: string;
}

export interface SystemReleaseCheck {
  status: string;
  release: SystemReleaseInfo;
  validation: SystemValidationResult;
  disaster_recovery: Record<string, unknown>;
  restore: Record<string, unknown>;
  backup_records: Record<string, unknown>[];
}
