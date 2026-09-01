import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DocumentAnalysisPanel } from "../components/investigation/DocumentAnalysisPanel";
import { SignatureVerificationPanel } from "../components/investigation/SignatureVerificationPanel";
import { TestProviders } from "./render";

const evidence = {
  id: "00000000-0000-0000-0000-000000000091",
  case_id: "00000000-0000-0000-0000-000000000092",
  evidence_number: "EVID-000091",
  original_filename: "invoice.pdf",
  stored_filename: "invoice.pdf",
  mime_type: "application/pdf",
  file_size: 512,
  sha256_hash: "a".repeat(64),
  status: "ANALYZED" as const,
  metadata: { classification: "DOCUMENT" },
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:01Z",
  custody_events: [],
};

const referenceEvidence = {
  ...evidence,
  id: "00000000-0000-0000-0000-000000000093",
  evidence_number: "EVID-000093",
  original_filename: "reference-signature.png",
  mime_type: "image/png",
};

const documentFinding = {
  id: "00000000-0000-0000-0000-000000000094",
  analysis_run_id: "00000000-0000-0000-0000-000000000095",
  detector: "metadata",
  category: "METADATA",
  severity: "INFO",
  method: "classical",
  confidence: 0.82,
  description: "PDF producer metadata present.",
  explanation: "Producer field indicates document tooling.",
  recommendation: null,
  model_name: "metadata_classical",
  model_version: "1.0.0",
  model_framework: "NATIVE",
  artifact_id: null,
  regions: [],
  metadata: {},
  created_at: "2026-08-31T00:00:02Z",
};

const signatureRun = {
  id: "00000000-0000-0000-0000-000000000096",
  reference_hash: "b".repeat(64),
  questioned_hash: "c".repeat(64),
  model: "siamese-signature",
  model_version: "1.0.0",
  similarity: null,
  threshold: 0.8,
  verdict: "UNAVAILABLE" as const,
  device: "cpu",
  processing_time_ms: 12.5,
  reference_evidence_id: referenceEvidence.id,
  questioned_evidence_id: evidence.id,
  localization: null,
  artifact_id: null,
  metadata: { status: "unavailable", reason: "SIGNATURE_MODEL_PATH is not configured." },
  created_at: "2026-08-31T00:00:03Z",
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
      if (url.includes("/document-analysis")) {
        return response({
          items: [
            {
              id: "00000000-0000-0000-0000-000000000095",
              evidence_id: evidence.id,
              status: "SUCCEEDED",
              engine_version: "1.0",
              device: "cpu",
              latency_ms: 55.2,
              findings_count: 1,
              created_at: "2026-08-31T00:00:01Z",
              started_at: "2026-08-31T00:00:01Z",
              completed_at: "2026-08-31T00:00:02Z",
              error_code: null,
              error_message: null,
              metadata: {
                detectors: [
                  {
                    name: "metadata",
                    model_name: "metadata_classical",
                    latency_ms: 8.1,
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
      if (url.includes("/document-findings")) {
        return response({
          items: [documentFinding],
          total: 1,
          limit: 100,
          offset: 0,
        });
      }
      if (url.includes("/signature-analysis")) {
        return response({
          items: [signatureRun],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      return response({ items: [], total: 0, limit: 50, offset: 0 });
    }),
  );
});

describe("Phase 6C document and signature panels", () => {
  it("shows document analysis controls, model metadata, and findings", async () => {
    render(
      <TestProviders>
        <DocumentAnalysisPanel evidence={evidence} />
      </TestProviders>,
    );

    expect(await screen.findByText("AI Document Analysis")).toBeInTheDocument();
    expect(screen.getByText("Run AI document analysis")).toBeInTheDocument();
    expect(await screen.findByText("SUCCEEDED")).toBeInTheDocument();
    expect(
      await screen.findByText(/metadata_classical v1\.0\.0/),
    ).toBeInTheDocument();
    expect(await screen.findByText(/82\.0%/)).toBeInTheDocument();
    expect(await screen.findByText(/PDF producer metadata present/)).toBeInTheDocument();
  });

  it("shows signature verification unavailable state and hash provenance", async () => {
    render(
      <TestProviders>
        <SignatureVerificationPanel
          evidence={evidence}
          referenceOptions={[evidence, referenceEvidence]}
        />
      </TestProviders>,
    );

    expect(await screen.findByText("Signature Verification")).toBeInTheDocument();
    expect(await screen.findByText("UNAVAILABLE")).toBeInTheDocument();
    expect(await screen.findByText(/Reference hash:/)).toBeInTheDocument();
    expect(await screen.findByText(/Questioned hash:/)).toBeInTheDocument();
    expect(
      await screen.findByText(/SIGNATURE_MODEL_PATH/),
    ).toBeInTheDocument();
  });
});
