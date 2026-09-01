import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { forensicsService } from "../services/api/forensics";

export function useEvidenceAnalysisQuery(evidenceId: string) {
  return useQuery({
    enabled: Boolean(evidenceId),
    queryKey: ["evidence", evidenceId, "analysis"],
    queryFn: () => forensicsService.listAnalysis(evidenceId),
    refetchInterval: (query) => {
      const latest = query.state.data?.data.items[0];
      return latest?.status === "QUEUED" || latest?.status === "RUNNING"
        ? 1000
        : false;
    },
  });
}

export function useEvidenceAnalysisSummaryQuery(evidenceId: string) {
  return useQuery({
    enabled: Boolean(evidenceId),
    queryKey: ["evidence", evidenceId, "analysis-summary"],
    queryFn: () => forensicsService.summary(evidenceId),
    refetchInterval: (query) => {
      const status = query.state.data?.data.status;
      return status === "QUEUED" || status === "RUNNING" ? 1000 : false;
    },
  });
}

export function useEvidenceFindingsQuery(evidenceId: string) {
  return useQuery({
    enabled: Boolean(evidenceId),
    queryKey: ["evidence", evidenceId, "findings"],
    queryFn: () => forensicsService.listFindings(evidenceId),
    staleTime: 10_000,
  });
}

export function useEvidenceHeatmapsQuery(evidenceId: string) {
  return useQuery({
    enabled: Boolean(evidenceId),
    queryKey: ["evidence", evidenceId, "heatmaps"],
    queryFn: () => forensicsService.listHeatmaps(evidenceId),
    staleTime: 15_000,
  });
}

export function useAnalyzeEvidenceMutation(evidenceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => forensicsService.analyze(evidenceId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "analysis"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "analysis-summary"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "findings"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "heatmaps"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "processing"],
      });
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}
