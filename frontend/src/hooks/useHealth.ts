import { useQuery } from "@tanstack/react-query";

import { healthService } from "../services/api/health";

export function useHealthQuery() {
  return useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => healthService.getHealth(signal),
    retry: 1,
    staleTime: 30_000,
  });
}

export function useSystemInfoQuery() {
  return useQuery({
    queryKey: ["system-info"],
    queryFn: ({ signal }) => healthService.getSystemInfo(signal),
    retry: 1,
    staleTime: 60_000,
  });
}

