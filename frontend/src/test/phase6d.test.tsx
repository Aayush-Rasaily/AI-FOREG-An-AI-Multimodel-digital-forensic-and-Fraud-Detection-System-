import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { VideoAnalysisPanel } from "../components/investigation/VideoAnalysisPanel";
import { TestProviders } from "./render";

const evidence = {
  id: "00000000-0000-0000-0000-000000000101",
  case_id: "00000000-0000-0000-0000-000000000102",
  evidence_number: "EVID-000101",
  original_filename: "clip.mp4",
  stored_filename: "clip.mp4",
  mime_type: "video/mp4",
  file_size: 512,
  sha256_hash: "d".repeat(64),
  status: "ANALYZED" as const,
  metadata: { classification: "VIDEO" },
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:01Z",
  custody_events: [],
};

const videoFinding = {
  id: "00000000-0000-0000-0000-000000000103",
  analysis_run_id: "00000000-0000-0000-0000-000000000104",
  detector: "deepfake",
  category: "DEEPFAKE",
  severity: "INFO",
  method: "ai",
  confidence: null,
  description: "deepfake capability unavailable.",
  explanation: "model_not_configured",
  recommendation: null,
  model_name: "video_deepfake",
  model_version: "1.0.0",
  model_framework: "NATIVE",
  temporal: null,
  artifact_id: null,
  regions: [],
  metadata: { status: "unavailable", reason: "model_not_configured" },
  limitations: "No trained model configured for this detector.",
  created_at: "2026-08-31T00:00:02Z",
};

function response(data: unknown) {
  return Promise.resolve({
    ok: true,
    json: async () => ({ success: true, data }),
  });
}

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  return input.url;
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = requestUrl(input);
      if (url.includes("/video-analysis/") && url.endsWith("/frames")) {
        return response([
          {
            frame_index: 0,
            frame_number: 1,
            timestamp_ms: 0,
            timestamp_seconds: 0,
            frame_id: "frame-1",
            artifact_id: null,
            width: 640,
            height: 360,
          },
        ]);
      }
      if (url.includes("/video-analysis/") && url.endsWith("/timeline")) {
        return response([
          {
            detector: "deepfake",
            category: "DEEPFAKE",
            severity: "INFO",
            confidence: null,
            method: "ai",
            start_frame: null,
            end_frame: null,
            start_timestamp_ms: null,
            end_timestamp_ms: null,
            description: "deepfake capability unavailable.",
          },
        ]);
      }
      if (url.includes("/video-analysis/00000000-0000-0000-0000-000000000104")) {
        return response({
          id: "00000000-0000-0000-0000-000000000104",
          evidence_id: evidence.id,
          status: "SUCCEEDED",
          engine_version: "1.0",
          device: "cpu",
          latency_ms: 88.4,
          findings_count: 1,
          created_at: "2026-08-31T00:00:01Z",
          started_at: "2026-08-31T00:00:01Z",
          completed_at: "2026-08-31T00:00:02Z",
          error_code: null,
          error_message: null,
          metadata: {
            detectors: [{ name: "deepfake", method: "ai", model_name: "video_deepfake" }],
            video: { duration_ms: 12000, fps: 30, frame_count: 360 },
          },
          video: { duration_ms: 12000, fps: 30, frame_count: 360 },
          timeline: [],
          frames: [],
          artifacts: [],
        });
      }
      if (url.includes("/video-analysis")) {
        return response({
          items: [
            {
              id: "00000000-0000-0000-0000-000000000104",
              evidence_id: evidence.id,
              status: "SUCCEEDED",
              engine_version: "1.0",
              device: "cpu",
              latency_ms: 88.4,
              findings_count: 1,
              created_at: "2026-08-31T00:00:01Z",
              started_at: "2026-08-31T00:00:01Z",
              completed_at: "2026-08-31T00:00:02Z",
              error_code: null,
              error_message: null,
              metadata: {
                detectors: [{ name: "deepfake", method: "ai" }],
                video: { duration_ms: 12000, fps: 30, frame_count: 360 },
              },
              video: { duration_ms: 12000, fps: 30, frame_count: 360 },
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      if (url.includes("/video-findings")) {
        return response({
          items: [videoFinding],
          total: 1,
          limit: 100,
          offset: 0,
        });
      }
      return response({ items: [], total: 0, limit: 50, offset: 0 });
    }),
  );
});

describe("Phase 6D video analysis panel", () => {
  it("shows video analysis controls, unavailable deepfake state, and findings", async () => {
    render(
      <TestProviders>
        <VideoAnalysisPanel evidence={evidence} />
      </TestProviders>,
    );

    expect(await screen.findByText("Video AI Analysis")).toBeInTheDocument();
    expect(screen.getByText("Run AI video analysis")).toBeInTheDocument();
    expect(await screen.findByText("SUCCEEDED")).toBeInTheDocument();
    expect(await screen.findByText(/deepfake capability unavailable/)).toBeInTheDocument();
    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
  });
});
