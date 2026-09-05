import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { platformValidationApi } from "../services/api/platformValidation";

export function usePlatformValidationLatestQuery() {
  return useQuery({
    queryKey: ["platform-validation", "latest"],
    queryFn: () => platformValidationApi.getLatest(),
  });
}

export function usePlatformReadinessQuery() {
  return useQuery({
    queryKey: ["platform-validation", "readiness"],
    queryFn: () => platformValidationApi.getReadiness(),
  });
}

export function usePlatformHealthReportQuery() {
  return useQuery({
    queryKey: ["platform-validation", "health"],
    queryFn: () => platformValidationApi.getHealthReport(),
  });
}

export function useRunPlatformValidationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => platformValidationApi.validate(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["platform-validation"],
      });
    },
  });
}
