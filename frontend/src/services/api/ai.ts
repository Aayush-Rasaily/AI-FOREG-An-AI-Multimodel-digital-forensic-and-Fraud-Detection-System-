import type { ApiResponse } from "../../types/api";
import type {
  AIModel,
  AIModelListData,
  InferenceJob,
  InferenceJobListData,
} from "../../types/ai";import { apiClient } from "./client";

export const aiService = {
  listModels: (limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<AIModelListData>>(
      `/models?limit=${limit}&offset=${offset}`,
    ),
  getModel: (modelId: string) =>
    apiClient.get<ApiResponse<AIModel>>(`/models/${modelId}`),
  reloadModel: (modelName: string) =>
    apiClient.postJson<ApiResponse<AIModel>>("/models/reload", {
      model_name: modelName,
    }),
  listJobs: (limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<InferenceJobListData>>(
      `/inference/jobs?limit=${limit}&offset=${offset}`,
    ),
  getJob: (jobId: string) =>
    apiClient.get<ApiResponse<InferenceJob>>(`/inference/jobs/${jobId}`),
};
