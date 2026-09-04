import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { systemService } from "../services/api/system";

export function useSystemVersionQuery() {
  return useQuery({
    queryKey: ["system-status", "version"],
    queryFn: () => systemService.getVersion(),
  });
}

export function useSystemReleaseQuery() {
  return useQuery({
    queryKey: ["system-status", "release"],
    queryFn: () => systemService.getRelease(),
  });
}

export function useSystemLivenessQuery() {
  return useQuery({
    queryKey: ["system-status", "liveness"],
    queryFn: () => systemService.getLiveness(),
  });
}

export function useSystemReadinessQuery() {
  return useQuery({
    queryKey: ["system-status", "readiness"],
    queryFn: () => systemService.getReadiness(),
  });
}

export function useSystemStartupValidationQuery() {
  return useQuery({
    queryKey: ["system-status", "startup-validation"],
    queryFn: () => systemService.getStartupValidation(),
  });
}

export function useSystemConfigurationQuery() {
  return useQuery({
    queryKey: ["system-status", "configuration"],
    queryFn: () => systemService.getConfiguration(),
  });
}

export function useSystemValidateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => systemService.validate(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["system-status"] });
    },
  });
}

export function useSystemReleaseCheckMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => systemService.releaseCheck(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["system-status"] });
    },
  });
}

export function useRefreshSystemStatus() {
  const queryClient = useQueryClient();
  return () =>
    queryClient.invalidateQueries({ queryKey: ["system-status"] });
}
