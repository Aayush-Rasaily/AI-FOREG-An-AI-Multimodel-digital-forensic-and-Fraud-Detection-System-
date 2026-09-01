export type CaseIntelligenceStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"
  | "CANCELLED";

export type CaseVerdict =
  | "genuine"
  | "suspicious"
  | "potential_fraud"
  | "inconclusive"
  | "insufficient_evidence"
  | "unavailable";

export type EvidenceCoverageStatus =
  | "not_analyzed"
  | "analyzed"
  | "inconclusive"
  | "insufficient_evidence"
  | "unavailable"
  | "failed";

export type RelationshipType =
  | "duplicate_hash"
  | "reference_link"
  | "comparison_link"
  | "signature_verification_link"
  | "shared_metadata"
  | "shared_filename";

export interface EvidenceCoverage {
  total_evidence: number;
  analyzed: number;
  not_analyzed: number;
  inconclusive: number;
  insufficient_evidence: number;
  unavailable: number;
  failed: number;
  supporting_evidence: number;
  contradictory_evidence: number;
  open_conflicts: number;
  supported_modalities: string[];
}

export interface EvidenceParticipation {
  evidence_id: string;
  evidence_number: string;
  evidence_type: string;
  evidence_hash: string;
  evidence_status: string;
  coverage_status: EvidenceCoverageStatus;
  fusion_run_id: string | null;
  fusion_verdict: CaseVerdict | null;
  risk_score: number | null;
  confidence: number | null;
  supporting_finding_ids: string[];
  contradictory_finding_ids: string[];
  conflicts_count: number;
  participating_modalities: string[];
  unavailable_modalities: string[];
  fusion_engine_version: string | null;
  fusion_policy_version: string | null;
  fusion_completed_at: string | null;
  reason?: string | null;
}

export interface CaseRelationship {
  id?: string;
  relationship_id: string;
  evidence_a_id: string;
  evidence_b_id: string;
  relationship_type: RelationshipType;
  confidence: number | null;
  supporting_reason: string;
  source_reference: string;
  status: string;
}

export interface CaseConflict {
  id?: string;
  conflict_id: string;
  conflict_type: string;
  severity: string;
  involved_evidence_ids: string[];
  involved_finding_ids: string[];
  explanation: string;
  resolution_status: string;
}

export interface TimelineEvent {
  id?: string;
  event_id: string;
  event_type: string;
  timestamp: string | null;
  timestamp_known: boolean;
  evidence_id: string | null;
  source_reference: string;
  description: string;
  metadata?: Record<string, unknown>;
}

export interface CaseIntelligenceRun {
  id: string;
  case_id: string;
  status: CaseIntelligenceStatus;
  engine_version: string;
  policy_version: string;
  verdict: CaseVerdict | null;
  risk_score: number | null;
  confidence: number | null;
  evidence_count: number;
  conflicts_count: number;
  relationships_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface CaseIntelligenceDetail extends CaseIntelligenceRun {
  coverage: EvidenceCoverage;
  participations: EvidenceParticipation[];
  relationships: CaseRelationship[];
  conflicts: CaseConflict[];
  timeline: TimelineEvent[];
  explanation: string | null;
  limitations: string | null;
  supporting_evidence_ids: string[];
  contradictory_evidence_ids: string[];
}

export interface CaseIntelligenceRunListData {
  items: CaseIntelligenceRun[];
  total: number;
  limit: number;
  offset: number;
}
