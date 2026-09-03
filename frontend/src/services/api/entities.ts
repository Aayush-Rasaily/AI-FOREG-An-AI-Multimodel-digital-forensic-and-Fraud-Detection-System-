import type { ApiResponse } from "../../types/api";
import type {
  CanonicalEntity,
  EntityDetail,
  EntityRelationship,
  EntityRun,
  EntityRunList,
  InvestigationGraph,
} from "../../types/entities";
import { apiClient } from "./client";

export const entitiesService = {
  generate: (caseId: string) =>
    apiClient.postJson<ApiResponse<EntityRun>>(`/cases/${caseId}/entities`, {}),
  listRuns: (caseId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<EntityRunList>>(
      `/cases/${caseId}/entities?limit=${limit}&offset=${offset}`,
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<EntityDetail>>(
      `/cases/${caseId}/entities/latest`,
    ),
  getEntity: (entityId: string) =>
    apiClient.get<ApiResponse<CanonicalEntity>>(`/entities/${entityId}`),
  getEntityGraph: (entityId: string) =>
    apiClient.get<ApiResponse<InvestigationGraph>>(
      `/entities/${entityId}/graph`,
    ),
  getEntityRelationships: (entityId: string) =>
    apiClient.get<ApiResponse<EntityRelationship[]>>(
      `/entities/${entityId}/relationships`,
    ),
};
