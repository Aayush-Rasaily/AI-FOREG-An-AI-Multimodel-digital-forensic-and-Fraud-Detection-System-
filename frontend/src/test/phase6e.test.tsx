import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AudioAnalysisPanel } from "../components/investigation/AudioAnalysisPanel";
import { TestProviders } from "./render";

const evidence = {
  id: "00000000-0000-0000-0000-000000000201",
  case_id: "00000000-0000-0000-0000-000000000202",
  evidence_number: "EVID-000201",
  original_filename: "sample.wav",
  stored_filename: "sample.wav",
  mime_type: "audio/wav",
  file_size: 512,
  sha256_hash: "e".repeat(64),
  status: "ANALYZED" as const,
  metadata: { classification: "AUDIO" },
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:01Z",
  custody_events: [],
};

const audioFinding = {
  id: "00000000-0000-0000-0000-000000000203",
  analysis_run_id: "00000000-0000-0000-0000-000000000204",
  detector: "synthetic_audio",
  category: "SYNTHETIC_AUDIO",
  severity: "INFO",
  method: "ai",
  confidence: null,
  description: "synthetic_audio capability unavailable.",
  explanation: "model_not_configured",
  recommendation: null,
  model_name: "audio_synthetic",
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
      if (url.includes("/audio-analysis/") && url.endsWith("/timeline")) {
        return response([
          {
            detector: "waveform",
            category: "WAVEFORM",
            severity: "LOW",
            confidence: 0.5,
            method: "classical",
            start_time_ms: 0,
            end_time_ms: 500,
            duration_ms: 500,
            description: "Amplitude discontinuity observed.",
          },
        ]);
      }
      if (url.includes("/audio-analysis/") && url.endsWith("/segments")) {
        return response([
          {
            segment_id: "waveform:0",
            detector: "waveform",
            category: "WAVEFORM",
            severity: "LOW",
            confidence: 0.5,
            start_time_ms: 0,
            end_time_ms: 500,
            duration_ms: 500,
            description: "Amplitude discontinuity observed.",
          },
        ]);
      }
      if (url.includes("/audio-analysis/") && !url.includes("/timeline")) {
        return response({
          id: "00000000-0000-0000-0000-000000000204",
          evidence_id: evidence.id,
          reference_evidence_id: null,
          status: "SUCCEEDED",
          engine_version: "1.0",
          device: "cpu",
          latency_ms: 12.5,
          findings_count: 1,
          created_at: "2026-08-31T00:00:00Z",
          started_at: "2026-08-31T00:00:00Z",
          completed_at: "2026-08-31T00:00:01Z",
          error_code: null,
          error_message: null,
          metadata: {
            audio: { sample_rate: 16000, channels: 1, codec: "wav" },
            detectors: [{ name: "waveform", method: "classical" }],
          },
          audio: { sample_rate: 16000, channels: 1, codec: "wav" },
          timeline: [],
          segments: [],
          features: {
            sample_rate: 16000,
            duration_seconds: 1.0,
            channels: 1,
            rms_energy: 0.1,
            zero_crossing_rate: 0.05,
            spectral_centroid_hz: 1200,
            mfcc_mean: [1, 2, 3],
            window_count: 4,
          },
          artifacts: [
            {
              id: "00000000-0000-0000-0000-000000000205",
              artifact_type: "AI_AUDIO_WAVEFORM",
              sha256_hash: "f".repeat(64),
              metadata: { points: 256 },
            },
          ],
        });
      }
      if (url.includes("/audio-findings")) {
        return response({ items: [audioFinding], total: 1, limit: 100, offset: 0 });
      }
      if (url.includes("/audio-analysis") && url.includes("/evidence/")) {
        return response({
          items: [
            {
              id: "00000000-0000-0000-0000-000000000204",
              evidence_id: evidence.id,
              reference_evidence_id: null,
              status: "SUCCEEDED",
              engine_version: "1.0",
              device: "cpu",
              latency_ms: 12.5,
              findings_count: 1,
              created_at: "2026-08-31T00:00:00Z",
              started_at: "2026-08-31T00:00:00Z",
              completed_at: "2026-08-31T00:00:01Z",
              error_code: null,
              error_message: null,
              metadata: {
                audio: { sample_rate: 16000, channels: 1, codec: "wav" },
                detectors: [{ name: "waveform", method: "classical" }],
              },
              audio: { sample_rate: 16000, channels: 1, codec: "wav" },
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      return response({});
    }),
  );
});

describe("AudioAnalysisPanel", () => {
  it("renders detector status and unavailable AI findings", async () => {
    render(
      <TestProviders>
        <AudioAnalysisPanel evidence={evidence} />
      </TestProviders>,
    );
    expect(await screen.findByText("Audio AI Analysis")).toBeInTheDocument();
    expect(await screen.findByText(/synthetic_audio capability unavailable/i)).toBeInTheDocument();
    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
    expect(await screen.findByText(/16000 Hz/i)).toBeInTheDocument();
  });
});
