import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "../routes/AppRoutes";
import { TestProviders } from "./render";

const caseRecord = {
  id: "00000000-0000-0000-0000-000000000031",
  case_number: "CASE-000031",
  title: "Forensic test",
  description: "Phase 5B",
  status: "OPEN",
  priority: "HIGH",
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:00Z",
};

const evidenceRecord = {
  id: "00000000-0000-0000-0000-000000000032",
  case_id: caseRecord.id,
  evidence_number: "EVID-000031",
  original_filename: "invoice.pdf",
  stored_filename: "original.pdf",
  mime_type: "application/pdf",
  file_size: 128,
  sha256_hash: "a".repeat(64),
  status: "ANALYZED",
  metadata: {},
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:00Z",
  custody_events: [],
};

const finding = {
  id: "00000000-0000-0000-0000-000000000033",
  analysis_run_id: "00000000-0000-0000-0000-000000000034",
  detector: "document_metadata",
  category: "METADATA",
  severity: "INFO",
  confidence: 0.85,
  description: "PDF producer metadata present.",
  explanation: "Producer field: pypdf",
  recommendation: null,
  regions: [],
  metadata: {},
  created_at: "2026-08-31T00:00:01Z",
};

function response(data: unknown) {
  return Promise.resolve({
    ok: true,
    json: async () => ({ success: true, data }),
  });
}

beforeEach(() => {
  let analyzed = true;
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith(`/cases/${caseRecord.id}`)) {
        return response(caseRecord);
      }
      if (url.includes(`/cases/${caseRecord.id}/evidence`)) {
        return response({ items: [evidenceRecord], total: 1 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/analysis-summary`)) {
        return response({
          status: analyzed ? "SUCCEEDED" : "QUEUED",
          analysis_run_id: "00000000-0000-0000-0000-000000000034",
          findings_count: analyzed ? 1 : 0,
          severity_counts: analyzed ? { INFO: 1 } : {},
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/analysis`)) {
        return response({
          items: analyzed
            ? [
                {
                  id: "00000000-0000-0000-0000-000000000034",
                  evidence_id: evidenceRecord.id,
                  status: "SUCCEEDED",
                  engine_version: "1.0",
                  findings_count: 1,
                  created_at: "2026-08-31T00:00:01Z",
                  started_at: "2026-08-31T00:00:01Z",
                  completed_at: "2026-08-31T00:00:02Z",
                  error_code: null,
                  error_message: null,
                  metadata: {},
                },
              ]
            : [],
          total: analyzed ? 1 : 0,
          limit: 50,
          offset: 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/findings`)) {
        return response({
          items: analyzed ? [finding] : [],
          total: analyzed ? 1 : 0,
          limit: 100,
          offset: 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/heatmaps`)) {
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/processing`)) {
        return response({ items: [], total: 0 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/extractions`)) {
        return response({
          status: "SUCCEEDED",
          error_code: null,
          items: [],
          total: 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/regions`)) {
        return response({ status: "SUCCEEDED", error_code: null, items: [], total: 0 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/extraction-artifacts`)) {
        return response({ items: [], total: 0 });
      }
      if (url.endsWith(`/evidence/${evidenceRecord.id}/analyze`)) {
        analyzed = true;
        return response({
          id: "00000000-0000-0000-0000-000000000035",
          evidence_id: evidenceRecord.id,
          job_type: "ANALYSIS",
          status: "QUEUED",
        });
      }
      if (url.includes(`/cases/${caseRecord.id}/references`)) {
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/comparison-summary`)) {
        return response({
          status: "SUCCEEDED",
          comparison_run_id: null,
          differences_count: 0,
          type_counts: {},
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/comparisons`)) {
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/differences`)) {
        return response({ items: [], total: 0, limit: 100, offset: 0 });
      }
      if (url.includes("/image-analysis") || url.includes("/image-findings")) {
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }
      if (
        url.includes("/document-analysis") ||
        url.includes("/document-findings")
      ) {
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }
      if (url.includes("/signature-analysis")) {
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }
      return response({ items: [], total: 0 });
    }),
  );
});

describe("Phase 5B forensic workspace", () => {
  it("shows analysis status, findings table, and detector details", async () => {
    render(
      <TestProviders initialEntries={[`/investigations/${caseRecord.id}`]}>
        <AppRoutes />
      </TestProviders>,
    );

    expect(await screen.findByText("SUCCEEDED")).toBeInTheDocument();
    expect(screen.getAllByText("document_metadata").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("PDF producer metadata present.").length,
    ).toBeGreaterThan(0);
  });
});
