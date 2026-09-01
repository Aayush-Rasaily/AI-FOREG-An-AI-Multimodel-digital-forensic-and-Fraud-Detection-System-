import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { imageAiService } from "../services/api/imageAi";

export function useImageAnalysisQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "image-analysis"],
    queryFn: () => imageAiService.listRuns(evidenceId),
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

export function useImageFindingsQuery(
  evidenceId: string,
  detector?: string,
) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "image-findings", detector ?? "all"],
    queryFn: () => imageAiService.listFindings(evidenceId, 100, 0, detector),
    enabled: Boolean(evidenceId),
    staleTime: 10_000,
  });
}

export function useAnalyzeImageMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (evidenceId: string) => imageAiService.analyze(evidenceId),
    onSuccess: (_data, evidenceId) => {
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "image-analysis"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "image-findings"],
      });
    },
  });
}
