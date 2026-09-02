import type { ApiResponse } from "../../types/api";
import type {
  TimelineConflict,
  TimelineDetail,
  TimelineRun,
  TimelineRunListData,
} from "../../types/timeline";
import { apiClient } from "./client";

export const timelineService = {
  generate: (caseId: string) =>
    apiClient.postJson<ApiResponse<TimelineRun>>(
      `/cases/${caseId}/timeline`,
      {},
    ),
  listTimelines: (caseId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<TimelineRunListData>>(
      `/cases/${caseId}/timeline?limit=${limit}&offset=${offset}`,
    ),
  getLatest: (caseId: string) =>
    apiClient.get<ApiResponse<TimelineDetail>>(
      `/cases/${caseId}/timeline/latest`,
    ),
  getTimeline: (timelineId: string) =>
    apiClient.get<ApiResponse<TimelineDetail>>(`/timeline/${timelineId}`),
  listConflicts: (timelineId: string) =>
    apiClient.get<ApiResponse<TimelineConflict[]>>(
      `/timeline/${timelineId}/conflicts`,
    ),
};
