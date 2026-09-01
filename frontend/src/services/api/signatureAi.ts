import type { ApiResponse } from "../../types/api";
import type { ProcessingJob } from "../../types/evidence";
import type {
  SignatureVerificationListData,
  SignatureVerificationRun,
} from "../../types/signatureAi";
import { apiClient } from "./client";

export const signatureAiService = {
  verify: (formData: FormData) =>
    apiClient.postForm<ApiResponse<SignatureVerificationRun>>(
      "/signature/verify",
      formData,
    ),
  queueAnalysis: (questionedEvidenceId: string, referenceEvidenceId: string) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${questionedEvidenceId}/signature-analysis`,
      { reference_evidence_id: referenceEvidenceId },
    ),
  listRuns: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<SignatureVerificationListData>>(
      `/evidence/${evidenceId}/signature-analysis?limit=${limit}&offset=${offset}`,
    ),
  getRun: (verificationId: string) =>
    apiClient.get<ApiResponse<SignatureVerificationRun>>(
      `/signature/${verificationId}`,
    ),
};
