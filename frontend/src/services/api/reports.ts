import type { ApiResponse } from "../../types/api";
import type {
  InvestigationReport,
  InvestigationReportDetail,
  InvestigationReportList,
  ReportDownloadFormat,
} from "../../types/reports";
import { apiClient } from "./client";

export const reportsService = {
  generate: (caseId: string) =>
    apiClient.postJson<ApiResponse<InvestigationReport>>(
      `/cases/${caseId}/reports`,
      {},
    ),
  listReports: (caseId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<InvestigationReportList>>(
      `/cases/${caseId}/reports?limit=${limit}&offset=${offset}`,
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<InvestigationReportDetail>>(
      `/cases/${caseId}/reports/latest`,
    ),
  getReport: (reportId: string) =>
    apiClient.get<ApiResponse<InvestigationReportDetail>>(
      `/reports/${reportId}`,
    ),
  downloadUrl: (reportId: string, format: ReportDownloadFormat = "json") =>
    `/api/v1/reports/${reportId}/download?format=${format}`,
};
