import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { audioAiService } from "../services/api/audioAi";
import type { AudioAnalysisRequest } from "../types/audioAi";

export function useAudioAnalysisQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "audio-analysis"],
    queryFn: () => audioAiService.listRuns(evidenceId),
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

export function useAudioFindingsQuery(
  evidenceId: string,
  detector?: string,
) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "audio-findings", detector ?? "all"],
    queryFn: () => audioAiService.listFindings(evidenceId, 100, 0, detector),
    enabled: Boolean(evidenceId),
    staleTime: 10_000,
  });
}

export function useAudioAnalysisDetailQuery(analysisId: string | undefined) {
  return useQuery({
    queryKey: ["audio-analysis", analysisId],
    queryFn: () => audioAiService.getRun(analysisId!),
    enabled: Boolean(analysisId),
    staleTime: 10_000,
  });
}

export function useAnalyzeAudioMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      evidenceId,
      body,
    }: {
      evidenceId: string;
      body?: AudioAnalysisRequest;
    }) => audioAiService.analyze(evidenceId, body),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["evidence", variables.evidenceId, "audio-analysis"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", variables.evidenceId, "audio-findings"],
      });
    },
  });
}
