import type { ApiResponse } from "../../types/api";
import type {
  GraphEntity,
  GraphPreview,
  KnowledgeGraph,
  NeighborResult,
} from "../../types/knowledgeGraph";
import { apiClient } from "./client";

export const knowledgeGraphApi = {
  build: (caseId: string) =>
    apiClient.postJson<ApiResponse<KnowledgeGraph>>(
      `/cases/${caseId}/knowledge-graph`,
      {},
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<KnowledgeGraph>>(
      `/cases/${caseId}/knowledge-graph`,
    ),
  preview: (caseId: string) =>
    apiClient.get<ApiResponse<GraphPreview>>(
      `/cases/${caseId}/knowledge-graph/preview`,
    ),
  getById: (graphId: string) =>
    apiClient.get<ApiResponse<KnowledgeGraph>>(
      `/knowledge-graph/${graphId}`,
    ),
  getEntity: (entityId: string) =>
    apiClient.get<ApiResponse<GraphEntity>>(
      `/knowledge-graph/entity/${entityId}`,
    ),
  getNeighbors: (entityId: string) =>
    apiClient.get<ApiResponse<NeighborResult>>(
      `/knowledge-graph/entity/${entityId}/neighbors`,
    ),
  search: (query: string, caseId?: string) => {
    const params = new URLSearchParams({ q: query });
    if (caseId) params.set("case_id", caseId);
    return apiClient.get<
      ApiResponse<{ items: GraphEntity[]; total: number }>
    >(`/knowledge-graph/search?${params.toString()}`);
  },
};
