export type GraphEntityType =
  | "PERSON"
  | "ORGANIZATION"
  | "EMAIL"
  | "PHONE"
  | "DEVICE"
  | "FILE"
  | "DOCUMENT"
  | "IMAGE"
  | "VIDEO"
  | "AUDIO"
  | "DOMAIN"
  | "URL"
  | "IP_ADDRESS"
  | "LOCATION"
  | "CASE"
  | "EVIDENCE"
  | "TIMELINE_EVENT"
  | "AI_FINDING"
  | "SIGNATURE"
  | "HASH"
  | "CAMERA"
  | "SOCIAL_ACCOUNT"
  | "LICENSE_PLATE"
  | "BANK_ACCOUNT"
  | "CRYPTO_WALLET"
  | string;

export interface GraphProvenanceItem {
  source_kind: string;
  source_id: string;
  evidence_id?: string | null;
  finding_id?: string | null;
  timeline_id?: string | null;
  correlation_id?: string | null;
  fusion_id?: string | null;
  ocr_field?: string | null;
  metadata_field?: string | null;
  timestamp?: string | null;
  detail?: string | null;
  engine_version?: string | null;
  policy_version?: string | null;
}

export interface GraphEntity {
  id: string;
  graph_id: string;
  case_id: string;
  entity_key: string;
  entity_type: GraphEntityType;
  display_name: string;
  normalized_key: string;
  confidence: number;
  attributes: Record<string, unknown>;
  evidence_ids: string[];
  aliases: string[];
  provenance: GraphProvenanceItem[];
}

export interface GraphRelationship {
  id: string;
  graph_id: string;
  case_id: string;
  relationship_key: string;
  source_entity_key: string;
  target_entity_key: string;
  relationship_type: string;
  confidence: number;
  support_count: number;
  provenance_count: number;
  relationship_weight: number;
  creation_source: string;
  evidence_ids: string[];
  attributes: Record<string, unknown>;
  provenance: GraphProvenanceItem[];
}

export interface KnowledgeGraph {
  id: string;
  case_id: string;
  status: string;
  entity_count: number;
  relationship_count: number;
  engine_version: string;
  policy_version: string;
  metadata: Record<string, unknown>;
  provenance: Record<string, unknown>;
  created_at: string;
  completed_at: string | null;
  entities: GraphEntity[];
  relationships: GraphRelationship[];
}

export interface GraphPreview {
  case_id: string;
  entity_count: number;
  relationship_count: number;
  entities: Record<string, unknown>[];
  relationships: Record<string, unknown>[];
  provenance: Record<string, unknown>;
  engine_version: string;
  policy_version: string;
  persisted: boolean;
}

export interface NeighborResult {
  entity: GraphEntity;
  relationships: GraphRelationship[];
  neighbors: GraphEntity[];
}
