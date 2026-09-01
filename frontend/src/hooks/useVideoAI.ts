import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { videoAiService } from "../services/api/videoAi";

export function useVideoAnalysisQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "video-analysis"],
    queryFn: () => videoAiService.listRuns(evidenceId),
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

export function useVideoFindingsQuery(
  evidenceId: string,
  detector?: string,
) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "video-findings", detector ?? "all"],
    queryFn: () => videoAiService.listFindings(evidenceId, 100, 0, detector),
    enabled: Boolean(evidenceId),
    staleTime: 10_000,
  });
}

export function useVideoAnalysisDetailQuery(analysisId: string | undefined) {
  return useQuery({
    queryKey: ["video-analysis", analysisId],
    queryFn: () => videoAiService.getRun(analysisId!),
    enabled: Boolean(analysisId),
    staleTime: 10_000,
  });
}

export function useAnalyzeVideoMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (evidenceId: string) => videoAiService.analyze(evidenceId),
    onSuccess: (_data, evidenceId) => {
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "video-analysis"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "video-findings"],
      });
    },
  });
}
