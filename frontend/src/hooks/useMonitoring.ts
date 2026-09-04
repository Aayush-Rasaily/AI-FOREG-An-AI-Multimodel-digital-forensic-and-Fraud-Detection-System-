import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { monitoringApi } from "../services/api/monitoring";

export function useMonitoringDashboardQuery() {
  return useQuery({
    queryKey: ["monitoring", "dashboard"],
    queryFn: () => monitoringApi.dashboard(),
  });
}

export function useRefreshMonitoringMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => monitoringApi.refresh(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["monitoring"] });
    },
  });
}
