import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { analyticsApi } from "../services/api/analytics";

export function useAnalyticsQuery() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: () => analyticsApi.getLatest(),
  });
}

export function useRefreshAnalyticsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => analyticsApi.refresh(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useAnalyticsExportMutation() {
  return useMutation({
    mutationFn: () => analyticsApi.export(),
  });
}
