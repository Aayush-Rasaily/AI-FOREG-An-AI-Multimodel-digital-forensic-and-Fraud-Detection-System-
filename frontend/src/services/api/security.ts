import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  CaseAccessRecord,
  ComplianceReport,
  PolicyViolation,
  SecurityListResponse,
  SecurityPermission,
  SecurityPolicy,
  SecurityRole,
  ValidationResult,
} from "../../types/security";

export const securityApi = {
  listRoles() {
    return apiClient.get<ApiResponse<SecurityListResponse<SecurityRole>>>(
      "/security/roles",
    );
  },

  listPermissions() {
    return apiClient.get<
      ApiResponse<SecurityListResponse<SecurityPermission>>
    >("/security/permissions");
  },

  getPolicy() {
    return apiClient.get<ApiResponse<SecurityPolicy>>("/security/policy");
  },

  listViolations(caseId?: string) {
    const query = caseId ? `?case_id=${caseId}` : "";
    return apiClient.get<ApiResponse<SecurityListResponse<PolicyViolation>>>(
      `/security/violations${query}`,
    );
  },

  validate(caseId?: string | null) {
    return apiClient.postJson<ApiResponse<ValidationResult>>(
      "/security/validate",
      { case_id: caseId ?? null },
    );
  },

  listCaseAccess(caseId: string) {
    return apiClient.get<ApiResponse<SecurityListResponse<CaseAccessRecord>>>(
      `/cases/${caseId}/access`,
    );
  },

  updateCaseAccess(
    caseId: string,
    payload: {
      user_id: string;
      access_level: string;
      reason?: string;
      active?: boolean;
    },
  ) {
    return apiClient.patchJson<ApiResponse<CaseAccessRecord>>(
      `/cases/${caseId}/access`,
      payload,
    );
  },

  getCompliance(caseId: string) {
    return apiClient.get<ApiResponse<ComplianceReport>>(
      `/cases/${caseId}/compliance`,
    );
  },
};
