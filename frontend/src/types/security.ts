export type ComplianceStatus = "COMPLIANT" | "PARTIAL" | "NON_COMPLIANT";

export interface SecurityRole {
  id?: string;
  code: string;
  name: string;
  description: string;
  permissions: string[];
  policy_version: string;
}

export interface SecurityPermission {
  id?: string;
  code: string;
  resource: string;
  action: string;
  description: string;
  roles: string[];
  policy_version: string;
}

export interface CaseAccessRecord {
  id: string;
  case_id: string;
  user_id: string;
  access_level: string;
  granted_by: string | null;
  reason: string | null;
  active: boolean;
  granted_at: string;
  revoked_at: string | null;
}

export interface ComplianceReport {
  status: ComplianceStatus | string;
  case_id: string | null;
  chain_of_custody_complete: boolean;
  evidence_integrity_ok: boolean;
  audit_complete: boolean;
  workflow_compliant: boolean;
  report_approval_compliant: boolean;
  missing_approvals: string[];
  missing_provenance: string[];
  policy_violations: string[];
  details: Record<string, unknown>;
  generated_at: string;
  policy_version: string;
  engine_version: string;
  report_id?: string | null;
}

export interface SecurityPolicy {
  policy_version: string;
  engine_version: string;
  case_retention_days: number;
  evidence_retention_days: number;
  report_publication_requires_approval: boolean;
  workflow_approval_required_for_archive: boolean;
  ai_execution_requires_case_access: boolean;
  export_requires_audit_view: boolean;
  policies: Array<{ code: string; description: string }>;
}

export interface PolicyViolation {
  id: string;
  case_id: string | null;
  policy_code: string;
  severity: string;
  message: string;
  details: Record<string, unknown>;
  detected_at: string;
  resolved_at: string | null;
  policy_version: string;
}

export interface ValidationFinding {
  check: string;
  status: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ValidationResult {
  status: ComplianceStatus | string;
  findings: ValidationFinding[];
  generated_at: string;
  policy_version: string;
  engine_version: string;
  case_id: string | null;
}

export interface SecurityListResponse<T> {
  items: T[];
  total: number;
}
