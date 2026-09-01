import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ImageAnalysisPanel } from "../components/investigation/ImageAnalysisPanel";
import { TestProviders } from "./render";

const evidence = {
  id: "00000000-0000-0000-0000-000000000081",
  case_id: "00000000-0000-0000-0000-000000000082",
  evidence_number: "EVID-000081",
  original_filename: "portrait.png",
  stored_filename: "portrait.png",
  mime_type: "image/png",
  file_size: 256,
  sha256_hash: "a".repeat(64),
  status: "ANALYZED" as const,
  metadata: { classification: "IMAGE" },
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:01Z",
  custody_events: [],
};

const imageFinding = {
  id: "00000000-0000-0000-0000-000000000083",
  analysis_run_id: "00000000-0000-0000-0000-000000000084",
  detector: "ai_generated",
  category: "AI_GENERATED",
  severity: "MEDIUM",
  confidence: 0.71,
  description: "Spectral patterns consistent with synthetic generation.",
  explanation: "High-frequency energy distribution differs from typical camera imagery.",
  recommendation: "Verify provenance.",
  model_name: "ai_generated_heuristic",
  model_version: "1.0.0",
  model_framework: "NATIVE",
  heatmap_artifact_id: "00000000-0000-0000-0000-000000000085",
  mask_artifact_id: null,
  regions: [{ x: 10, y: 10, width: 20, height: 20, page_number: null, frame_number: null, polygon: null, normalized_location: null }],
  metadata: {},
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
      if (url.includes("/image-analysis")) {
        return response({
          items: [
            {
              id: "00000000-0000-0000-0000-000000000084",
              evidence_id: evidence.id,
              status: "SUCCEEDED",
              engine_version: "1.0",
              device: "cpu",
              latency_ms: 42.5,
              findings_count: 1,
              created_at: "2026-08-31T00:00:01Z",
              started_at: "2026-08-31T00:00:01Z",
              completed_at: "2026-08-31T00:00:02Z",
              error_code: null,
              error_message: null,
              metadata: {
                detectors: [
                  {
                    name: "ai_generated",
                    model_name: "ai_generated_heuristic",
                    latency_ms: 12.3,
                  },
                ],
              },
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      if (url.includes("/image-findings")) {
        return response({
          items: [imageFinding],
          total: 1,
          limit: 100,
          offset: 0,
        });
      }
      return response({ items: [], total: 0, limit: 50, offset: 0 });
    }),
  );
});

describe("Phase 6B AI image analysis panel", () => {
  it("shows analysis controls, model metadata, and findings", async () => {
    render(
      <TestProviders>
        <ImageAnalysisPanel evidence={evidence} />
      </TestProviders>,
    );

    expect(await screen.findByText("AI Image Analysis")).toBeInTheDocument();
    expect(screen.getByText("Run AI image analysis")).toBeInTheDocument();
    expect(await screen.findByText("SUCCEEDED")).toBeInTheDocument();
    expect(await screen.findByText(/ai_generated_heuristic v1\.0\.0/)).toBeInTheDocument();
    expect(await screen.findByText(/71\.0%/)).toBeInTheDocument();
    expect(await screen.findByText(/Spectral patterns/)).toBeInTheDocument();
  });
});
