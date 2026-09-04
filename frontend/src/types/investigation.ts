export type InvestigationTab =
  | "overview"
  | "evidence"
  | "forensics"
  | "comparison"
  | "findings"
  | "timeline"
  | "correlations"
  | "entities"
  | "jury"
  | "metadata"
  | "report"
  | "summary"
  | "audit"
  | "collaboration"
  | "workflow"
  | "security";

export type FindingState =
  | "confirmed"
  | "strong-suspicion"
  | "suspicious"
  | "informational";

export type EvidenceKind =
  | "image"
  | "pdf"
  | "video"
  | "audio"
  | "document"
  | "signature";

export interface Finding {
  type: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  confidence: number;
  description: string;
  location?: string;
  evidenceSource?: string;
  engine?: string;
  timestamp?: string;
  supportingEvidence?: string[];
  state: FindingState;
}

