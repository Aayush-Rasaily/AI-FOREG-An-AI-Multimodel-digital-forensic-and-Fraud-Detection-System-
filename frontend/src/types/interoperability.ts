export type ExportFormat =
  | "json_package"
  | "csv"
  | "pdf_bundle"
  | "zip_evidence"
  | "manifest";

export interface ExportJob {
  id: string;
  case_id: string;
  format: string;
  status: string;
  package_version: string;
  schema_version: string;
  storage_key: string | null;
  package_checksum: string | null;
  manifest_checksum: string | null;
  evidence_ids: string[];
  report_versions: string[];
  timeline_version: string | null;
  policy_versions: Record<string, string>;
  error_message: string | null;
  created_by: string | null;
  engine_version: string;
  policy_version: string;
  created_at: string;
  completed_at: string | null;
}

export interface ExportJobList {
  items: ExportJob[];
  total: number;
}

export interface ImportJob {
  id: string;
  source_filename: string | null;
  status: string;
  package_version: string | null;
  schema_version: string | null;
  integrity_status: string;
  validation: {
    valid?: boolean;
    integrity_status?: string;
    findings?: { check: string; status: string; message: string }[];
    package_version?: string | null;
    schema_version?: string | null;
  };
  conflicts: string[];
  package_checksum: string | null;
  storage_key: string | null;
  target_case_id: string | null;
  error_message: string | null;
  created_by: string | null;
  engine_version: string;
  policy_version: string;
  created_at: string;
  completed_at: string | null;
}

export interface ImportJobList {
  items: ImportJob[];
  total: number;
}

export interface PackageManifest {
  export_job_id: string;
  manifest: Record<string, unknown>;
  manifest_checksum: string;
  package_checksum: string;
}

export interface ExportRequest {
  format: ExportFormat | string;
  evidence_ids?: string[] | null;
  include_binaries?: boolean;
}
