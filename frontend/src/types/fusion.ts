export type FusionModality =
  | "forensics"
  | "image_ai"
  | "document_ai"
  | "signature_ai"
  | "video_ai"
  | "audio_ai"
  | "comparison";

export type ModalityAvailability =
  | "available"
  | "unavailable"
  | "not_applicable"
  | "failed"
  | "insufficient_evidence";

export type FusionVerdict =
  | "genuine"
  | "suspicious"
  | "potential_fraud"
  | "inconclusive"
  | "insufficient_evidence"
  | "unavailable";

export type FusionRunStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"
  | "UNAVAILABLE"
  | "CANCELLED";

export type JuryMemberRole =
  | "forensic_analyst"
  | "document_image_specialist"
  | "multimedia_specialist"
  | "signature_specialist"
  | "consistency_analyst"
  | "senior_judge";

export type ConflictType =
  | "verdict_disagreement"
  | "confidence_disagreement"
  | "modality_disagreement"
  | "temporal_inconsistency"
  | "provenance_inconsistency"
  | "contradictory_finding";

export interface ModalityStatus {
  modality: FusionModality;
  availability: ModalityAvailability;
  findings_count: number;
  reason?: string | null;
}

export interface JuryAssessment {
  id?: string;
  role: JuryMemberRole;
  member_name: string;
  verdict: FusionVerdict;
  confidence: number | null;
  availability: ModalityAvailability;
  supporting_finding_ids: string[];
  contradictory_finding_ids: string[];
  explanation: string;
  limitations?: string | null;
  model_name?: string;
  model_version?: string;
}

export interface FusionConflict {
  id?: string;
  conflict_id: string;
  conflict_type: ConflictType;
  severity: string;
  involved_finding_ids: string[];
  involved_modalities: string[];
  explanation: string;
  resolution_status: string;
}

export interface AgreementMetrics {
  modality_agreement_ratio: number;
  jury_agreement_ratio: number;
  supporting_modalities: number;
  contradictory_modalities: number;
  unavailable_modalities: number;
  inconclusive_modalities: number;
  confidence_spread: number | null;
  jury_votes_available: number;
  jury_votes_total: number;
}

export interface FusionAnalysisRun {
  id: string;
  evidence_id: string;
  status: FusionRunStatus;
  engine_version: string;
  policy_version: string;
  verdict: FusionVerdict | null;
  risk_score: number | null;
  confidence: number | null;
  findings_count: number;
  conflicts_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface FusionAnalysisDetail extends FusionAnalysisRun {
  modality_status: ModalityStatus[];
  jury_assessments: JuryAssessment[];
  conflicts: FusionConflict[];
  agreement: AgreementMetrics | null;
  explanation: string | null;
  limitations: string | null;
  supporting_finding_ids: string[];
  contradictory_finding_ids: string[];
  participating_modalities: FusionModality[];
  unavailable_modalities: FusionModality[];
}

export interface FusionAnalysisRunListData {
  items: FusionAnalysisRun[];
  total: number;
  limit: number;
  offset: number;
}

export interface NormalizedFinding {
  finding_id: string;
  evidence_id: string;
  modality: FusionModality;
  analyzer: string;
  category: string;
  finding_type: string;
  verdict: string;
  confidence: number | null;
  severity: string;
  description: string;
  explanation: string;
  source_reference: string;
  availability: ModalityAvailability;
  model_name?: string;
  model_version?: string;
  temporal?: Record<string, unknown> | null;
  metadata?: Record<string, unknown>;
}

export interface FusionSignalsData {
  evidence_id: string;
  findings: NormalizedFinding[];
  modality_status: ModalityStatus[];
}
