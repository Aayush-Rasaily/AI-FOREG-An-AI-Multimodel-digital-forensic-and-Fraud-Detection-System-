import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { InvestigationSummaryPanel } from "../components/investigation/InvestigationSummaryPanel";
import { TestProviders } from "./render";

const caseId = "00000000-0000-0000-0000-000000000c8c";

const summary = {
  id: "s1",
  case_id: caseId,
  generated_at: "2026-09-03T00:00:00Z",
  overall_risk: "medium",
  overall_confidence: 42,
  overview: {
    evidence_count: 2,
    analyzed_count: 1,
    not_analyzed_count: 1,
    mime_types: { "application/pdf": 2 },
  },
  key_findings: [],
  timeline_summary: { available: true, event_count: 3 },
  correlation_summary: { available: true, correlation_count: 1 },
  ai_summary: {
    modality_counts: { image: 0, document: 1, signature: 0, video: 0, audio: 0 },
    fusion: { run_count: 1, agreement: 1, conflicts_count: 0 },
  },
  recommendations: [
    {
      code: "export_report",
      title: "Export report",
      rationale: "Export a Phase 6H forensic report.",
      supporting_finding_refs: [],
      provenance: {
        evidence_ids: [],
        finding_ids: [],
        fusion_ids: [],
        timeline_ids: [],
        correlation_ids: [],
        entity_ids: [],
        report_ids: [],
        audit_ids: [],
      },
    },
  ],
  provenance: {},
  narrative: [
    {
      section: "case_overview",
      text: "Case contains 2 evidence item(s).",
      provenance: {
        evidence_ids: [],
        finding_ids: [],
        fusion_ids: [],
        timeline_ids: [],
        correlation_ids: [],
        entity_ids: [],
        report_ids: [],
        audit_ids: [],
      },
    },
  ],
  engine_version: "8c.1.0",
  policy_version: "8c.1.0",
};

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () =>
      status >= 200 && status < 300
        ? { success: true, data }
        : {
            success: false,
            error: {
              message: "Not found.",
              code: "NOT_FOUND",
              request_id: null,
            },
          },
  });
}

describe("Phase 8C investigation summary frontend", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/investigation-summaries/latest")) {
          return response(summary);
        }
        return response({});
      }),
    );
  });

  it("renders summary narrative risk confidence and sections", async () => {
    render(
      <TestProviders>
        <InvestigationSummaryPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(
      await screen.findByText("Investigation summary"),
    ).toBeInTheDocument();
    expect(await screen.findByText(/Risk: medium/i)).toBeInTheDocument();
    expect(await screen.findByText(/Confidence: 42\/100/i)).toBeInTheDocument();
    expect(
      await screen.findByText("Case contains 2 evidence item(s)."),
    ).toBeInTheDocument();
    expect(await screen.findByText(/Events: 3/i)).toBeInTheDocument();
    expect(await screen.findByText(/Correlations: 1/i)).toBeInTheDocument();
    expect(await screen.findByText(/Fusion runs:/i)).toBeInTheDocument();
    expect(await screen.findByText("Export report")).toBeInTheDocument();
  });

  it("renders empty state when no summary exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async () => response({}, 404)),
    );
    render(
      <TestProviders>
        <InvestigationSummaryPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("No summary yet")).toBeInTheDocument();
    expect(await screen.findByText("Generate summary")).toBeInTheDocument();
  });
});
