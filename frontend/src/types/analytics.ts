export interface AnalyticsMetric {
  key: string;
  label: string;
  value: number;
  unit: string;
  category: string;
  provenance: Record<string, unknown>;
}

export interface AnalyticsRun {
  id?: string | null;
  status: string;
  metric_count: number;
  metrics: AnalyticsMetric[];
  sections: Record<string, unknown>;
  trends: Record<string, Array<{ index: number; label: string; value: number }>>;
  dashboard: Record<string, unknown>;
  provenance: Record<string, unknown>;
  engine_version: string;
  policy_version: string;
  created_at?: string | null;
  completed_at?: string | null;
  persisted: boolean;
}

export interface AnalyticsSection {
  section: string;
  data: Record<string, unknown>;
  engine_version: string;
  policy_version: string;
  generated_at?: string | null;
}

export interface AnalyticsExport {
  format: string;
  generated_at: string;
  engine_version: string;
  policy_version: string;
  payload: Record<string, unknown>;
}
