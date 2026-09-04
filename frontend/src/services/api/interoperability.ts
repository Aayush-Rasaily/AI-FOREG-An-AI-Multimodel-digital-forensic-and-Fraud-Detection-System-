import type { ApiResponse } from "../../types/api";
import type {
  ExportJob,
  ExportJobList,
  ExportRequest,
  ImportJob,
  ImportJobList,
  PackageManifest,
} from "../../types/interoperability";
import { apiClient } from "./client";
import { appConfig } from "../../config/env";
import { getAccessToken } from "./tokenStore";

export const interoperabilityApi = {
  exportCase: (caseId: string, body: ExportRequest) =>
    apiClient.postJson<ApiResponse<ExportJob>>(
      `/cases/${caseId}/export`,
      body,
    ),
  listExports: (caseId?: string) => {
    const query = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
    return apiClient.get<ApiResponse<ExportJobList>>(`/exports${query}`);
  },
  getExport: (exportId: string) =>
    apiClient.get<ApiResponse<ExportJob>>(`/exports/${exportId}`),
  getManifest: (exportId: string) =>
    apiClient.get<ApiResponse<PackageManifest>>(
      `/exports/${exportId}/manifest`,
    ),
  listImports: () =>
    apiClient.get<ApiResponse<ImportJobList>>("/imports"),
  getImport: (importId: string) =>
    apiClient.get<ApiResponse<ImportJob>>(`/imports/${importId}`),
  importPackage: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.postForm<ApiResponse<ImportJob>>("/cases/import", form);
  },
  downloadUrl: (exportId: string) =>
    `${appConfig.apiBaseUrl}/exports/${exportId}/download`,
  downloadExport: async (exportId: string) => {
    const token = getAccessToken();
    const response = await fetch(
      `${appConfig.apiBaseUrl}/exports/${exportId}/download`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      },
    );
    if (!response.ok) {
      throw new Error("Download failed");
    }
    return response.blob();
  },
};
