export interface IntegrityMetrics {
  checks_total: number;
  checks_passed: number;
  checks_failed: number;
  checks_warned: number;
  alert_count: number;
  drift_count: number;
  evidence_coverage_pct: number;
  integrity_score: number;
  critical_alerts: number;
  high_alerts: number;
}

export interface IntegrityCheck {
  id?: string | null;
  check_key: string;
  check_code: string;
  title: string;
  status: string;
  severity: string;
  evidence_id?: string | null;
  message: string;
  expected?: string | null;
  observed?: string | null;
  provenance: Record<string, unknown>;
}

export interface IntegrityAlert {
  id?: string | null;
  alert_key: string;
  alert_code: string;
  severity: string;
  title: string;
  message: string;
  evidence_id?: string | null;
  check_code?: string | null;
  provenance: Record<string, unknown>;
}

export interface IntegrityDrift {
  id?: string | null;
  drift_key: string;
  evidence_id: string;
  field_name: string;
  previous_value?: string | null;
  current_value?: string | null;
  message: string;
  provenance: Record<string, unknown>;
}

export interface IntegrityRun {
  id?: string | null;
  case_id: string;
  status: string;
  check_count: number;
  alert_count: number;
  drift_count: number;
  metrics: IntegrityMetrics;
  timeline: Array<Record<string, unknown>>;
  fingerprints: Record<string, unknown>;
  provenance: Record<string, unknown>;
  engine_version: string;
  policy_version: string;
  created_at?: string | null;
  completed_at?: string | null;
  checks: IntegrityCheck[];
  alerts: IntegrityAlert[];
  drifts: IntegrityDrift[];
  persisted: boolean;
}

export interface IntegrityHistoryItem {
  id: string;
  case_id: string;
  status: string;
  check_count: number;
  alert_count: number;
  drift_count: number;
  metrics: IntegrityMetrics;
  engine_version: string;
  policy_version: string;
  created_at: string;
  completed_at?: string | null;
}
