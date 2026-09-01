import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { comparisonService } from "../services/api/comparison";

export function useCaseReferencesQuery(caseId: string) {
  return useQuery({
    enabled: Boolean(caseId),
    queryKey: ["cases", caseId, "references"],
    queryFn: () => comparisonService.listReferences(caseId),
    staleTime: 10_000,
  });
}

export function useRegisterReferenceMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      evidence_id: string;
      label: string;
      description?: string;
    }) => comparisonService.registerReference(caseId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["cases", caseId, "references"],
      });
    },
  });
}

export function useEvidenceComparisonSummaryQuery(evidenceId: string) {
  return useQuery({
    enabled: Boolean(evidenceId),
    queryKey: ["evidence", evidenceId, "comparison-summary"],
    queryFn: () => comparisonService.summary(evidenceId),
    refetchInterval: (query) => {
      const status = query.state.data?.data.status;
      return status === "QUEUED" || status === "RUNNING" ? 1000 : false;
    },
  });
}

export function useEvidenceComparisonsQuery(evidenceId: string) {
  return useQuery({
    enabled: Boolean(evidenceId),
    queryKey: ["evidence", evidenceId, "comparisons"],
    queryFn: () => comparisonService.listComparisons(evidenceId),
    refetchInterval: (query) => {
      const latest = query.state.data?.data.items[0];
      return latest?.status === "QUEUED" || latest?.status === "RUNNING"
        ? 1000
        : false;
    },
  });
}

export function useEvidenceDifferencesQuery(evidenceId: string) {
  return useQuery({
    enabled: Boolean(evidenceId),
    queryKey: ["evidence", evidenceId, "differences"],
    queryFn: () => comparisonService.listDifferences(evidenceId),
    staleTime: 10_000,
  });
}

export function useCompareEvidenceMutation(evidenceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (referenceEvidenceId: string) =>
      comparisonService.compare(evidenceId, referenceEvidenceId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "comparisons"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "comparison-summary"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "differences"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "processing"],
      });
    },
  });
}
