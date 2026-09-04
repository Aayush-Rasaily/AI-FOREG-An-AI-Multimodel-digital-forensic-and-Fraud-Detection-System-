import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { investigationIntelligenceApi } from "../services/api/investigationIntelligence";

export function useInvestigationIntelligenceQuery(caseId: string) {
  return useQuery({
    queryKey: ["investigation-intelligence", caseId],
    queryFn: () => investigationIntelligenceApi.getLatest(caseId),
    retry: false,
  });
}

export function useAnalyzeInvestigationIntelligenceMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => investigationIntelligenceApi.analyze(caseId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["investigation-intelligence", caseId],
      });
    },
  });
}

export function useInvestigationPreviewQuery(caseId: string, enabled = false) {
  return useQuery({
    queryKey: ["investigation-intelligence", caseId, "preview"],
    queryFn: () => investigationIntelligenceApi.preview(caseId),
    enabled,
  });
}

export function useInvestigationCaseSummaryQuery(caseId: string) {
  return useQuery({
    queryKey: ["investigation-intelligence", caseId, "summary"],
    queryFn: () => investigationIntelligenceApi.getSummary(caseId),
  });
}
