import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { timelineService } from "../services/api/timeline";
import type { TimelineRun } from "../types/timeline";
import { ApiClientError } from "../services/api/client";

export function useTimelineHistoryQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "timeline-history"],
    queryFn: () => timelineService.listTimelines(caseId),
    enabled: Boolean(caseId),
    staleTime: 10_000,
    refetchInterval: (query) => {
      const items = query.state.data?.data.items ?? [];
      const active = items.some(
        (item: TimelineRun) => item.status === "QUEUED" || item.status === "RUNNING",
      );
      return active ? 1000 : false;
    },
  });
}

export function useTimelineLatestQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "timeline-latest"],
    queryFn: () => timelineService.getLatest(caseId),
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
      return status === "QUEUED" || status === "RUNNING" ? 1000 : false;
    },
  });
}

export function useGenerateTimelineMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId }: { caseId: string }) => timelineService.generate(caseId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "timeline-history"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["case", variables.caseId, "timeline-latest"],
      });
    },
  });
}

export function useTimelineConflictsQuery(timelineId: string | undefined) {
  return useQuery({
    queryKey: ["timeline", timelineId, "conflicts"],
    queryFn: () => timelineService.listConflicts(timelineId!),
    enabled: Boolean(timelineId),
    staleTime: 10_000,
  });
}
