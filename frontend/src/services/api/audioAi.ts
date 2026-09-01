import type { ApiResponse } from "../../types/api";
import type {
  AudioAIFindingListData,
  AudioAnalysisDetail,
  AudioAnalysisRequest,
  AudioAnalysisRunListData,
  AudioFeatureSummary,
  AudioSegment,
  AudioTimelineEntry,
} from "../../types/audioAi";
import type { ProcessingJob } from "../../types/evidence";
import { apiClient } from "./client";

export const audioAiService = {
  analyze: (evidenceId: string, body: AudioAnalysisRequest = {}) =>
    apiClient.postJson<ApiResponse<ProcessingJob>>(
      `/evidence/${evidenceId}/audio-analysis`,
      body,
    ),
  listRuns: (evidenceId: string, limit = 50, offset = 0) =>
    apiClient.get<ApiResponse<AudioAnalysisRunListData>>(
      `/evidence/${evidenceId}/audio-analysis?limit=${limit}&offset=${offset}`,
    ),
  getRun: (analysisId: string) =>
    apiClient.get<ApiResponse<AudioAnalysisDetail>>(
      `/audio-analysis/${analysisId}`,
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
    return apiClient.get<ApiResponse<AudioAIFindingListData>>(
      `/evidence/${evidenceId}/audio-findings?${params.toString()}`,
    );
  },
  listTimeline: (analysisId: string) =>
    apiClient.get<ApiResponse<AudioTimelineEntry[]>>(
      `/audio-analysis/${analysisId}/timeline`,
    ),
  listSegments: (analysisId: string) =>
    apiClient.get<ApiResponse<AudioSegment[]>>(
      `/audio-analysis/${analysisId}/segments`,
    ),
  getFeatures: (analysisId: string) =>
    apiClient.get<ApiResponse<AudioFeatureSummary | null>>(
      `/audio-analysis/${analysisId}/features`,
    ),
};
