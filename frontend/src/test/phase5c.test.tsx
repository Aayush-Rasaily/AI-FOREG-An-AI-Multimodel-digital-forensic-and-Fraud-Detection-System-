import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "../routes/AppRoutes";
import { TestProviders } from "./render";

const caseRecord = {
  id: "00000000-0000-0000-0000-000000000041",
  case_number: "CASE-000041",
  title: "Comparison test",
  description: "Phase 5C",
  status: "OPEN",
  priority: "HIGH",
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:00Z",
};

const evidenceRecord = {
  id: "00000000-0000-0000-0000-000000000042",
  case_id: caseRecord.id,
  evidence_number: "EVID-000041",
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

const referenceRecord = {
  id: "00000000-0000-0000-0000-000000000043",
  case_id: caseRecord.id,
  evidence_id: "00000000-0000-0000-0000-000000000044",
  label: "Trusted reference",
  description: null,
  reference_hash: "b".repeat(64),
  original_filename: "reference.pdf",
  mime_type: "application/pdf",
  metadata: {},
  created_at: "2026-08-31T00:00:00Z",
};

const difference = {
  id: "00000000-0000-0000-0000-000000000045",
  comparison_run_id: "00000000-0000-0000-0000-000000000046",
  matcher: "text",
  difference_type: "NUMBER_CHANGED",
  severity: "HIGH",
  confidence: 0.9,
  description: "Numeric value changed between reference and submitted text.",
  explanation: "12500 -> 72500",
  original_value: "12500",
  submitted_value: "72500",
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
  let compared = true;
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
      if (url.includes(`/cases/${caseRecord.id}/references`)) {
        return response({
          items: [referenceRecord],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/comparison-summary`)) {
        return response({
          status: compared ? "SUCCEEDED" : "QUEUED",
          comparison_run_id: "00000000-0000-0000-0000-000000000046",
          differences_count: compared ? 1 : 0,
          type_counts: compared ? { NUMBER_CHANGED: 1 } : {},
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/comparisons`)) {
        return response({
          items: compared
            ? [
                {
                  id: "00000000-0000-0000-0000-000000000046",
                  evidence_id: evidenceRecord.id,
                  reference_evidence_id: referenceRecord.evidence_id,
                  reference_record_id: referenceRecord.id,
                  status: "SUCCEEDED",
                  engine_version: "1.0",
                  differences_count: 1,
                  created_at: "2026-08-31T00:00:01Z",
                  started_at: "2026-08-31T00:00:01Z",
                  completed_at: "2026-08-31T00:00:02Z",
                  error_code: null,
                  error_message: null,
                  metadata: {},
                },
              ]
            : [],
          total: compared ? 1 : 0,
          limit: 50,
          offset: 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/differences`)) {
        return response({
          items: compared ? [difference] : [],
          total: compared ? 1 : 0,
          limit: 100,
          offset: 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/analysis-summary`)) {
        return response({
          status: "SUCCEEDED",
          analysis_run_id: null,
          findings_count: 0,
          severity_counts: {},
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/findings`)) {
        return response({ items: [], total: 0, limit: 100, offset: 0 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/heatmaps`)) {
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/analysis`)) {
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
      if (url.endsWith(`/evidence/${evidenceRecord.id}/compare`)) {
        compared = true;
        return response({
          id: "00000000-0000-0000-0000-000000000047",
          evidence_id: evidenceRecord.id,
          job_type: "COMPARISON",
          status: "QUEUED",
        });
      }
      return response({ items: [], total: 0 });
    }),
  );
});

describe("Phase 5C comparison workspace", () => {
  it("shows comparison status, reference selector, and difference table", async () => {
    render(
      <TestProviders initialEntries={[`/investigations/${caseRecord.id}`]}>
        <AppRoutes />
      </TestProviders>,
    );

    expect((await screen.findAllByText("Reference comparison")).length).toBeGreaterThan(
      0,
    );
    expect(await screen.findByText("SUCCEEDED")).toBeInTheDocument();
    expect(
      screen.getAllByText("Numeric value changed between reference and submitted text.")
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("12500")).toBeInTheDocument();
    expect(screen.getByText("72500")).toBeInTheDocument();
  });
});
