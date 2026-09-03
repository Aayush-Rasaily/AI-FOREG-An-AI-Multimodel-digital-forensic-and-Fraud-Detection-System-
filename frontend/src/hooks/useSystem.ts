import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { systemService } from "../services/api/system";

export function useSystemHealthQuery() {
  return useQuery({
    queryKey: ["system", "health"],
    queryFn: () => systemService.getHealth(),
    staleTime: 15_000,
  });
}

export function useSystemMetricsQuery() {
  return useQuery({
    queryKey: ["system", "metrics"],
    queryFn: () => systemService.getMetrics(),
    staleTime: 15_000,
  });
}

export function useSystemJobsQuery() {
  return useQuery({
    queryKey: ["system", "jobs"],
    queryFn: () => systemService.getJobs(),
    staleTime: 10_000,
  });
}

export function useSystemStorageQuery() {
  return useQuery({
    queryKey: ["system", "storage"],
    queryFn: () => systemService.getStorage(),
    staleTime: 30_000,
  });
}

export function useSystemDiagnosticsQuery() {
  return useQuery({
    queryKey: ["system", "diagnostics"],
    queryFn: () => systemService.getDiagnostics(),
    staleTime: 30_000,
  });
}

export function useRunDiagnosticsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => systemService.runDiagnostics(),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["system", "diagnostics"],
      });
    },
  });
}

export function useRefreshSystemDashboard() {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries({ queryKey: ["system"] });
  };
}
