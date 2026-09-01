import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { caseIntelligenceService } from "../services/api/caseIntelligence";

export function useCaseIntelligenceQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "intelligence"],
    queryFn: () => caseIntelligenceService.listRuns(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    refetchInterval: (query) => {
      const items = query.state.data?.data.items ?? [];
      const active = items.some(
        (item) => item.status === "QUEUED" || item.status === "RUNNING",
      );
      return active ? 1000 : false;
    },
  });
}

export function useCaseIntelligenceLatestQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "intelligence-latest"],
    queryFn: () => caseIntelligenceService.getLatest(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes("404")) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function useCaseTimelineQuery(caseId: string, enabled = true) {
  return useQuery({
    queryKey: ["case", caseId, "timeline"],
    queryFn: () => caseIntelligenceService.listTimeline(caseId),
    enabled: Boolean(caseId) && enabled,
    staleTime: 10_000,
    retry: false,
  });
}

export function useAnalyzeCaseIntelligenceMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId }: { caseId: string }) =>
      caseIntelligenceService.analyze(caseId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "intelligence"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "intelligence-latest"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "timeline"],
      });
    },
  });
}
