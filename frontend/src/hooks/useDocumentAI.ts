import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { documentAiService } from "../services/api/documentAi";

export function useDocumentAnalysisQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "document-analysis"],
    queryFn: () => documentAiService.listRuns(evidenceId),
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

export function useDocumentFindingsQuery(
  evidenceId: string,
  detector?: string,
) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "document-findings", detector ?? "all"],
    queryFn: () => documentAiService.listFindings(evidenceId, 100, 0, detector),
    enabled: Boolean(evidenceId),
    staleTime: 10_000,
  });
}

export function useAnalyzeDocumentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (evidenceId: string) => documentAiService.analyze(evidenceId),
    onSuccess: (_data, evidenceId) => {
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "document-analysis"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "document-findings"],
      });
    },
  });
}
