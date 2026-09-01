import type { ApiResponse } from "../../types/api";
import type {
  ForensicReport,
  ForensicReportDetail,
  ForensicReportListData,
  ForensicReportStatus,
} from "../../types/forensicReport";
import { apiClient } from "./client";

export const forensicReportService = {
  generate: (caseId: string) =>
    apiClient.postJson<ApiResponse<ForensicReport>>(
      `/cases/${caseId}/reports`,
      {},
    ),
  listReports: (caseId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<ForensicReportListData>>(
      `/cases/${caseId}/reports?limit=${limit}&offset=${offset}`,
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<ForensicReportDetail>>(
      `/cases/${caseId}/reports/latest`,
    ),
  getReport: (reportId: string) =>
    apiClient.get<ApiResponse<ForensicReportDetail>>(`/reports/${reportId}`),
  getStatus: (reportId: string) =>
    apiClient.get<ApiResponse<ForensicReportStatus>>(
      `/reports/${reportId}/status`,
    ),
  downloadUrl: (reportId: string) => `/api/v1/reports/${reportId}/download`,
};
