import type { ApiResponse } from "../../types/api";
import type {
  AuditEvent,
  AuditEventList,
  IntegrityVerifyResult,
} from "../../types/audit";
import { apiClient } from "./client";

export const auditService = {
  listEvents: (params?: {
    operation?: string;
    category?: string;
    limit?: number;
    offset?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.operation) q.set("operation", params.operation);
    if (params?.category) q.set("category", params.category);
    q.set("limit", String(params?.limit ?? 50));
    q.set("offset", String(params?.offset ?? 0));
    return apiClient.get<ApiResponse<AuditEventList>>(
      `/audit?${q.toString()}`,
    );
  },
  getEvent: (eventId: string) =>
    apiClient.get<ApiResponse<AuditEvent>>(`/audit/${eventId}`),
  listForCase: (caseId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<AuditEventList>>(
      `/cases/${caseId}/audit?limit=${limit}&offset=${offset}`,
    ),
  listForEvidence: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<AuditEventList>>(
      `/evidence/${evidenceId}/audit?limit=${limit}&offset=${offset}`,
    ),
  verify: (params: {
    case_id?: string;
    evidence_id?: string;
    report_id?: string;
  }) => {
    const q = new URLSearchParams();
    if (params.case_id) q.set("case_id", params.case_id);
    if (params.evidence_id) q.set("evidence_id", params.evidence_id);
    if (params.report_id) q.set("report_id", params.report_id);
    return apiClient.postJson<ApiResponse<IntegrityVerifyResult>>(
      `/audit/verify?${q.toString()}`,
      {},
    );
  },
  exportUrl: (caseId?: string) => {
    const q = caseId ? `?case_id=${caseId}` : "";
    return `/api/v1/audit/export${q}`;
  },
};
