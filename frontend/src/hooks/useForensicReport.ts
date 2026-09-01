import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { forensicReportService } from "../services/api/forensicReport";
import type { ForensicReport } from "../types/forensicReport";

export function useForensicReportsQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "reports"],
    queryFn: () => forensicReportService.listReports(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    refetchInterval: (query) => {
      const items = query.state.data?.data.items ?? [];
      const active = items.some(
        (item: ForensicReport) =>
          item.status === "QUEUED" || item.status === "GENERATING",
      );
      return active ? 1000 : false;
    },
  });
}

export function useForensicReportLatestQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "reports-latest"],
    queryFn: () => forensicReportService.getLatest(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes("404")) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function useGenerateForensicReportMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId }: { caseId: string }) =>
      forensicReportService.generate(caseId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "reports"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "reports-latest"],
      });
    },
  });
}
