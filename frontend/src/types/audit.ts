export interface AuditEvent {
  id: string;
  timestamp: string;
  user: string;
  operation: string;
  category: string;
  case_id: string | null;
  evidence_id: string | null;
  previous_state: unknown;
  new_state: unknown;
  client_ip: string | null;
  user_agent: string | null;
  engine_version: string;
  policy_version: string;
  sha256_checksum: string | null;
  integrity_hash: string;
  metadata: Record<string, unknown>;
}

export interface AuditEventList {
  items: AuditEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface IntegrityResult {
  target_type: string;
  target_id: string;
  status: string;
  expected_hash: string | null;
  computed_hash: string | null;
  detail: string;
}

export interface IntegrityVerifyResult {
  results: IntegrityResult[];
  overall_status: string;
  verified_count: number;
  mismatch_count: number;
  unavailable_count: number;
}
