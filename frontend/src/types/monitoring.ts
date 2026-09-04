export type PlatformHealthStatus =
  | "HEALTHY"
  | "DEGRADED"
  | "WARNING"
  | "CRITICAL";

export interface SystemHealth {
  status: PlatformHealthStatus | string;
  reasons: string[];
  signals: Record<string, number | string>;
  assessed_at: string;
  engine_version: string;
  policy_version: string;
}

export interface MonitoringDashboard {
  system_health: SystemHealth;
  processing: Record<string, unknown>;
  ai: Record<string, unknown>;
  cases: Record<string, unknown>;
  reports: Record<string, unknown>;
  api: Record<string, unknown>;
  activity: Record<string, unknown>;
  bottlenecks: Record<string, unknown>;
  audit_summary: Record<string, unknown>;
  kpis: Record<string, unknown>;
  trends: Record<string, unknown>;
  recent_failures: Array<Record<string, unknown>>;
  generated_at: string;
  engine_version: string;
  policy_version: string;
  snapshot_id?: string | null;
}

export interface MonitoringSection {
  data: Record<string, unknown>;
  generated_at: string;
  engine_version: string;
  policy_version: string;
}

export interface MonitoringRefresh {
  snapshot_id: string;
  health_record_id: string;
  audit_statistics_id: string;
  generated_at: string;
  system_health: SystemHealth;
  engine_version: string;
  policy_version: string;
}
