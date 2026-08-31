import type { ApiResponse } from "../../types/api";
import type {
  ArtifactListData,
  ProcessingJob,
  ProcessingJobListData,
} from "../../types/evidence";
import { apiClient } from "./client";

export const processingService = {
  process: (evidenceId: string) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${evidenceId}/process`,
      {},
    ),
  listJobs: (evidenceId: string, limit = 20, offset = 0) =>
    apiClient.get<ApiResponse<ProcessingJobListData>>(
      `/evidence/${evidenceId}/processing?limit=${limit}&offset=${offset}`,
    ),
  listArtifacts: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<ArtifactListData>>(
      `/evidence/${evidenceId}/artifacts?limit=${limit}&offset=${offset}`,
    ),
  getJob: (jobId: string) =>
    apiClient.get<ApiResponse<ProcessingJob>>(`/processing/${jobId}`),
};
