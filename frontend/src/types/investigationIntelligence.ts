export interface CoverageMetrics {
  evidence_total: number;
  evidence_analyzed: number;
  evidence_pending: number;
  timeline_coverage: number;
  knowledge_graph_coverage: number;
  correlation_coverage: number;
  fusion_coverage: number;
  ai_coverage: number;
  metadata_completeness: number;
  chain_of_custody_completeness: number;
  overall_completeness: number;
  open_conflicts: number;
}

export interface Hypothesis {
  id?: string | null;
  run_id?: string | null;
  case_id?: string | null;
  hypothesis_key: string;
  hypothesis_type: string;
  title: string;
  explanation: string;
  confidence: number;
  priority: string;
  status: string;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  provenance: Record<string, unknown>;
  attributes: Record<string, unknown>;
}

export interface EvidenceGap {
  id?: string | null;
  run_id?: string | null;
  case_id?: string | null;
  gap_key: string;
  gap_type: string;
  severity: string;
  reason: string;
  recommended_action: string;
  affected_evidence_ids: string[];
  provenance: Record<string, unknown>;
}

export interface IntelligenceRecommendation {
  id?: string | null;
  run_id?: string | null;
  case_id?: string | null;
  recommendation_key: string;
  code: string;
  action_text: string;
  priority: string;
  related_hypothesis_keys: string[];
  related_gap_keys: string[];
  affected_evidence_ids: string[];
  provenance: Record<string, unknown>;
}

export interface IntelligenceRun {
  id?: string | null;
  case_id: string;
  status: string;
  investigation_score: number;
  overall_completeness: number;
  hypothesis_count: number;
  gap_count: number;
  recommendation_count: number;
  open_conflict_count: number;
  coverage: CoverageMetrics;
  open_conflicts: Array<Record<string, unknown>>;
  provenance: Record<string, unknown>;
  engine_version: string;
  policy_version: string;
  created_at?: string | null;
  completed_at?: string | null;
  hypotheses: Hypothesis[];
  gaps: EvidenceGap[];
  recommendations: IntelligenceRecommendation[];
  persisted: boolean;
}

export interface InvestigationCaseSummary {
  case_id: string;
  run_id?: string | null;
  investigation_score: number;
  overall_completeness: number;
  coverage: CoverageMetrics;
  top_hypotheses: Hypothesis[];
  critical_gaps: EvidenceGap[];
  top_recommendations: IntelligenceRecommendation[];
  open_conflicts: Array<Record<string, unknown>>;
  engine_version: string;
  policy_version: string;
}
