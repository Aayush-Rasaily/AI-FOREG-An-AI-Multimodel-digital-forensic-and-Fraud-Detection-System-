export type VizTone =
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "neutral"
  | "info";

export interface VizSlice {
  id: string;
  label: string;
  value: number;
  tone?: VizTone;
  meta?: string;
}

export interface VizSeriesPoint {
  id: string;
  label: string;
  value: number;
}

export interface GraphNode {
  id: string;
  label: string;
  kind:
    | "case"
    | "evidence"
    | "timeline"
    | "fusion"
    | "correlation"
    | "report";
  detail?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

export const VIZ_TONE_FILL: Record<VizTone, string> = {
  primary: "var(--color-primary, #2563eb)",
  success: "var(--color-success, #16a34a)",
  warning: "var(--color-warning, #d97706)",
  danger: "var(--color-danger, #dc2626)",
  neutral: "var(--color-muted, #64748b)",
  info: "var(--color-info, #0891b2)",
};

export interface AnalyticsFilterState {
  dateFrom: string;
  dateTo: string;
  evidenceType: string;
  risk: string;
  confidenceMin: number;
  status: string;
  caseId: string;
  aiModality: string;
  correlationType: string;
  selectedSliceId: string | null;
}

export const DEFAULT_ANALYTICS_FILTERS: AnalyticsFilterState = {
  dateFrom: "",
  dateTo: "",
  evidenceType: "all",
  risk: "all",
  confidenceMin: 0,
  status: "all",
  caseId: "all",
  aiModality: "all",
  correlationType: "all",
  selectedSliceId: null,
};
