import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiClientError } from "../services/api/client";
import { correlationService } from "../services/api/correlation";
import type { CorrelationRun } from "../types/correlation";

export function useCorrelationHistoryQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "correlation-history"],
    queryFn: () => correlationService.listRuns(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    refetchInterval: (query) => {
      const items = query.state.data?.data.items ?? [];
      const active = items.some(
        (item: CorrelationRun) =>
          item.status === "QUEUED" || item.status === "RUNNING",
      );
      return active ? 1000 : false;
    },
  });
}

export function useCorrelationLatestQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "correlation-latest"],
    queryFn: () => correlationService.getLatest(caseId),
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

export function useGenerateCorrelationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId }: { caseId: string }) =>
      correlationService.generate(caseId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "correlation-history"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "correlation-latest"],
      });
    },
  });
}

export function useEvidenceCorrelationsQuery(evidenceId: string | undefined) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "correlations"],
    queryFn: () => correlationService.listForEvidence(evidenceId!),
    enabled: Boolean(evidenceId),
    staleTime: 10_000,
  });
}
