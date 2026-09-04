import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { knowledgeGraphApi } from "../services/api/knowledgeGraph";

export function useKnowledgeGraphQuery(caseId: string) {
  return useQuery({
    queryKey: ["knowledge-graph", caseId],
    queryFn: () => knowledgeGraphApi.getLatest(caseId),
    retry: false,
  });
}

export function useKnowledgeGraphPreviewQuery(caseId: string, enabled = false) {
  return useQuery({
    queryKey: ["knowledge-graph", caseId, "preview"],
    queryFn: () => knowledgeGraphApi.preview(caseId),
    enabled,
  });
}

export function useBuildKnowledgeGraphMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => knowledgeGraphApi.build(caseId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["knowledge-graph", caseId],
      });
    },
  });
}

export function useGraphEntityQuery(entityId: string | null) {
  return useQuery({
    queryKey: ["knowledge-graph", "entity", entityId],
    queryFn: () => knowledgeGraphApi.getEntity(entityId!),
    enabled: Boolean(entityId),
  });
}

export function useGraphNeighborsQuery(entityId: string | null) {
  return useQuery({
    queryKey: ["knowledge-graph", "neighbors", entityId],
    queryFn: () => knowledgeGraphApi.getNeighbors(entityId!),
    enabled: Boolean(entityId),
  });
}

export function useGraphSearchQuery(query: string, caseId?: string) {
  return useQuery({
    queryKey: ["knowledge-graph", "search", caseId, query],
    queryFn: () => knowledgeGraphApi.search(query, caseId),
    enabled: query.trim().length > 0,
  });
}
