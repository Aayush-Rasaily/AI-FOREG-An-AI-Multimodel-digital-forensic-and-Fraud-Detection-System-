import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiClientError } from "../services/api/client";
import { entitiesService } from "../services/api/entities";
import type { EntityRun } from "../types/entities";

export function useEntityHistoryQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "entity-history"],
    queryFn: () => entitiesService.listRuns(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    refetchInterval: (query) => {
      const items = query.state.data?.data.items ?? [];
      const active = items.some(
        (item: EntityRun) => item.status === "QUEUED" || item.status === "RUNNING",
      );
      return active ? 1000 : false;
    },
  });
}

export function useEntityLatestQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "entity-latest"],
    queryFn: () => entitiesService.getLatest(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiClientError && error.status === 404) {
        return false;
      }
      return failureCount < 2;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.data.status;
      return status === "QUEUED" || status === "RUNNING" ? 1000 : false;
    },
  });
}

export function useGenerateEntitiesMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId }: { caseId: string }) =>
      entitiesService.generate(caseId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "entity-history"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "entity-latest"],
      });
    },
  });
}
