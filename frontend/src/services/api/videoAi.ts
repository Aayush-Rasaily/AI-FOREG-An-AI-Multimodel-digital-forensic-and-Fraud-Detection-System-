import type { ApiResponse } from "../../types/api";
import type {
  VideoAIFindingListData,
  VideoAnalysisDetail,
  VideoAnalysisRunListData,
  VideoFrame,
  VideoTimelineEntry,
} from "../../types/videoAi";
import type { ProcessingJob } from "../../types/evidence";
import { apiClient } from "./client";

export const videoAiService = {
  analyze: (evidenceId: string) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${evidenceId}/video-analysis`,
      {},
    ),
  listRuns: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<VideoAnalysisRunListData>>(
      `/evidence/${evidenceId}/video-analysis?limit=${limit}&offset=${offset}`,
    ),
  getRun: (analysisId: string) =>
    apiClient.get<ApiResponse<VideoAnalysisDetail>>(
      `/video-analysis/${analysisId}`,
    ),
  listFindings: (
    evidenceId: string,
    limit = 100,
    offset = 0,
    detector?: string,
  ) => {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    if (detector) {
      params.set("detector", detector);
    }
    return apiClient.get<ApiResponse<VideoAIFindingListData>>(
      `/evidence/${evidenceId}/video-findings?${params.toString()}`,
    );
  },
  listFrames: (analysisId: string) =>
    apiClient.get<ApiResponse<VideoFrame[]>>(
      `/video-analysis/${analysisId}/frames`,
    ),
  listTimeline: (analysisId: string) =>
    apiClient.get<ApiResponse<VideoTimelineEntry[]>>(
      `/video-analysis/${analysisId}/timeline`,
    ),
};
