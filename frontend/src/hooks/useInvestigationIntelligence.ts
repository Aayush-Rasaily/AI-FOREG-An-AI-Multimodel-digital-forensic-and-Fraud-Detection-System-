import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { intelligenceApi } from "../services/api/intelligence";
import { ApiClientError } from "../services/api/client";

export function useInvestigationSummaryLatestQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "investigation-summary-latest"],
    queryFn: async () => {
      try {
        return await intelligenceApi.latest(caseId);
      } catch (error) {
        if (error instanceof ApiClientError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
    enabled: Boolean(caseId),
  });
}

export function useGenerateInvestigationSummaryMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => intelligenceApi.generate(caseId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case", caseId, "investigation-summary-latest"],
      });
    },
  });
}
