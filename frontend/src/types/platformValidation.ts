export interface ValidationResult {
  check_key: string;
  category: string;
  label: string;
  status: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ValidationIssue {
  check_key: string;
  category: string;
  severity: string;
  message: string;
  details: Record<string, unknown>;
}

export interface PlatformValidationRun {
  id?: string | null;
  status: string;
  readiness_score: number;
  readiness_level: string;
  check_count: number;
  pass_count: number;
  warn_count: number;
  fail_count: number;
  results: ValidationResult[];
  issues: ValidationIssue[];
  health_report: Record<string, unknown>;
  compatibility: Record<string, unknown>;
  provenance: Record<string, unknown>;
  engine_version: string;
  policy_version: string;
  created_at?: string | null;
  completed_at?: string | null;
  persisted: boolean;
}

export interface PlatformReadiness {
  readiness_score: number;
  readiness_level: string;
  check_count: number;
  pass_count: number;
  warn_count: number;
  fail_count: number;
  engine_version: string;
  policy_version: string;
  generated_at?: string | null;
  persisted: boolean;
  run_id?: string | null;
}

export interface HealthReport {
  report: Record<string, unknown>;
  engine_version: string;
  policy_version: string;
  persisted: boolean;
  run_id?: string | null;
}

export interface ValidationList {
  runs: PlatformValidationRun[];
  engine_version: string;
  policy_version: string;
}
