import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fusionService } from "../services/api/fusion";

export function useFusionAnalysisQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "fusion-analysis"],
    queryFn: () => fusionService.listRuns(evidenceId),
    enabled: Boolean(evidenceId),
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

export function useFusionLatestQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "fusion-latest"],
    queryFn: () => fusionService.getLatest(evidenceId),
    enabled: Boolean(evidenceId),
    staleTime: 10_000,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes("404")) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function useFusionJuryQuery(evidenceId: string, enabled = true) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "fusion-jury"],
    queryFn: () => fusionService.listJury(evidenceId),
    enabled: Boolean(evidenceId) && enabled,
    staleTime: 10_000,
    retry: false,
  });
}

export function useFusionConflictsQuery(evidenceId: string, enabled = true) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "fusion-conflicts"],
    queryFn: () => fusionService.listConflicts(evidenceId),
    enabled: Boolean(evidenceId) && enabled,
    staleTime: 10_000,
    retry: false,
  });
}

export function useAnalyzeFusionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ evidenceId }: { evidenceId: string }) =>
      fusionService.analyze(evidenceId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["evidence", variables.evidenceId, "fusion-analysis"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", variables.evidenceId, "fusion-latest"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", variables.evidenceId, "fusion-jury"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", variables.evidenceId, "fusion-conflicts"],
      });
    },
  });
}
