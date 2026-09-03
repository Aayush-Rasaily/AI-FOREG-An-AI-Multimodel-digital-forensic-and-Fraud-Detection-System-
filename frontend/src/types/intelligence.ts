export type CaseRiskLevel = "low" | "medium" | "high" | "critical";

export interface ProvenanceLinks {
  evidence_ids: string[];
  finding_ids: string[];
  fusion_ids: string[];
  timeline_ids: string[];
  correlation_ids: string[];
  entity_ids: string[];
  report_ids: string[];
  audit_ids: string[];
}

export interface NarrativeParagraph {
  section: string;
  text: string;
  provenance: ProvenanceLinks;
}

export interface RecommendationItem {
  code: string;
  title: string;
  rationale: string;
  supporting_finding_refs: string[];
  provenance: ProvenanceLinks;
}

export interface InvestigationSummary {
  id: string;
  case_id: string;
  generated_at: string;
  overall_risk: CaseRiskLevel | string;
  overall_confidence: number;
  overview: Record<string, unknown>;
  key_findings: Array<Record<string, unknown>>;
  timeline_summary: Record<string, unknown>;
  correlation_summary: Record<string, unknown>;
  ai_summary: Record<string, unknown>;
  recommendations: RecommendationItem[];
  provenance: Record<string, unknown>;
  narrative: NarrativeParagraph[];
  engine_version: string;
  policy_version: string;
}

export interface InvestigationSummaryList {
  items: InvestigationSummary[];
  total: number;
  limit: number;
  offset: number;
}
