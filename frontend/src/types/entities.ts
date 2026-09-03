export type EntityRunStatus = "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED";

export type EntityType =
  | "person"
  | "organization"
  | "email"
  | "phone"
  | "address"
  | "website"
  | "domain"
  | "device"
  | "camera"
  | "vehicle"
  | "bank_account"
  | "crypto_wallet"
  | "document"
  | "image"
  | "video"
  | "audio"
  | "qr_code"
  | "logo"
  | "signature"
  | "location"
  | "ip_address"
  | "file_hash";

export type RelationshipType =
  | "owns"
  | "uses"
  | "created"
  | "contains"
  | "references"
  | "sent_to"
  | "received_from"
  | "captured_by"
  | "signed_by"
  | "located_at"
  | "related_to"
  | "derived_from"
  | "duplicate_of"
  | "supports"
  | "contradicts";

export interface EntitySupport {
  id: string;
  support_kind: string;
  support_ref: string;
  label: string;
  value: string | null;
  metadata: Record<string, unknown>;
}

export interface CanonicalEntity {
  id: string;
  analysis_run_id: string;
  case_id: string;
  canonical_id: string;
  entity_type: EntityType;
  display_name: string;
  normalized_key: string;
  confidence: number;
  support_count: number;
  evidence_ids: string[];
  attributes: Record<string, unknown>;
  provenance: Record<string, unknown>;
  supports: EntitySupport[];
  created_at: string;
}

export interface EntityRelationship {
  id: string;
  analysis_run_id: string;
  case_id: string;
  relationship_id: string;
  source_canonical_id: string;
  target_canonical_id: string;
  relationship_type: RelationshipType;
  confidence: number;
  support_count: number;
  explanation: string;
  evidence_ids: string[];
  provenance: Record<string, unknown>;
  supports: EntitySupport[];
  created_at: string;
}

export interface InvestigationGraph {
  nodes: CanonicalEntity[];
  edges: EntityRelationship[];
  provenance: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface EntityRun {
  id: string;
  case_id: string;
  status: EntityRunStatus;
  engine_version: string;
  policy_version: string;
  entity_count: number;
  relationship_count: number;
  evidence_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface EntityDetail extends EntityRun {
  entities: CanonicalEntity[];
  relationships: EntityRelationship[];
  graph: InvestigationGraph;
}

export interface EntityRunList {
  items: EntityRun[];
  total: number;
  limit: number;
  offset: number;
}
