import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiClientError } from "../services/api/client";
import { reportsService } from "../services/api/reports";
import type { InvestigationReport } from "../types/reports";

export function useReportHistoryQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "report-history"],
    queryFn: () => reportsService.listReports(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    refetchInterval: (query) => {
      const items = query.state.data?.data.items ?? [];
      const active = items.some(
        (item: InvestigationReport) =>
          item.status === "QUEUED" || item.status === "GENERATING",
      );
      return active ? 1000 : false;
    },
  });
}

export function useReportLatestQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "report-latest"],
    queryFn: () => reportsService.getLatest(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiClientError && error.status === 404) {
        return false;
      }
      return failureCount < 2;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.data.status;
      return status === "QUEUED" || status === "GENERATING" ? 1000 : false;
    },
  });
}

export function useGenerateReportMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId }: { caseId: string }) =>
      reportsService.generate(caseId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "report-history"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "report-latest"],
      });
    },
  });
}
