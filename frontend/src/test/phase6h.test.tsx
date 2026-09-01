import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ForensicReportPanel } from "../components/investigation/ForensicReportPanel";
import { TestProviders } from "./render";

const caseId = "00000000-0000-0000-0000-000000000601";
const emptyCaseId = "00000000-0000-0000-0000-000000000699";

const reportDetail = {
  id: "00000000-0000-0000-0000-000000000602",
  case_id: caseId,
  status: "COMPLETED" as const,
  report_version: "1.0",
  engine_version: "1.0",
  fusion_policy_version: "1.0",
  case_intelligence_policy_version: "1.0",
  case_intelligence_run_id: "00000000-0000-0000-0000-000000000603",
  evidence_count: 1,
  evidence_hashes: ["a".repeat(64)],
  pdf_sha256: "b".repeat(64),
  has_pdf: true,
  created_at: "2026-08-31T00:00:00Z",
  started_at: "2026-08-31T00:00:00Z",
  completed_at: "2026-08-31T00:00:01Z",
  error_code: null,
  error_message: null,
  metadata: {},
  provenance: { report_sha256: "b".repeat(64) },
  content: {
    sections: {
      executive_summary: {
        case_verdict: "suspicious",
        risk_score: 72,
        confidence: 0.81,
        evidence_count: 1,
      },
      evidence_inventory: [
        {
          evidence_id: "00000000-0000-0000-0000-000000000604",
          evidence_number: "EVID-001",
          filename: "statement.pdf",
          coverage_status: "analyzed",
        },
      ],
      multimodal_jury_assessment: [
        {
          evidence_id: "00000000-0000-0000-0000-000000000604",
          evidence_number: "EVID-001",
          verdict: "suspicious",
        },
      ],
      conflicts_and_contradictions: [
        {
          conflict_id: "verdict:1",
          conflict_type: "verdict_disagreement",
          explanation: "Evidence items disagree on fusion verdicts.",
        },
      ],
      investigation_timeline: [
        {
          event_id: "registered:1",
          description: "Evidence EVID-001 registered.",
        },
      ],
      confidence_and_limitations: {
        limitations: ["Case synthesis aggregates Phase 6F fusion results."],
      },
      explainability: {
        why: "Case verdict: suspicious.",
        jury_note: "AI/system-generated assessments.",
        conflicts: [],
      },
    },
  },
  executive_summary: {
    case_verdict: "suspicious",
    risk_score: 72,
    confidence: 0.81,
    evidence_count: 1,
  },
  explainability: {
    why: "Case verdict: suspicious.",
    jury_note: "AI/system-generated assessments.",
    conflicts: [],
  },
};

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => ({ success: true, data }),
  });
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/reports/latest")) {
        return response(reportDetail);
      }
      return response({});
    }),
  );
});

describe("ForensicReportPanel", () => {
  it("renders completed report preview and download action", async () => {
    render(
      <TestProviders>
        <ForensicReportPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("COMPLETED")).toBeInTheDocument();
    expect(screen.getAllByText(/suspicious/i).length).toBeGreaterThan(0);
    expect(screen.getByText("EVID-001")).toBeInTheDocument();
    expect(screen.getByText(/Download PDF/i)).toBeInTheDocument();
    expect(screen.getByText(/verdict disagreement/i)).toBeInTheDocument();
    expect(screen.getByText(/AI\/system-generated assessments/i)).toBeInTheDocument();
  });

  it("renders empty state when no report exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: false,
          status: 404,
          json: async () => ({
            success: false,
            error: { code: "NOT_FOUND", message: "No forensic report exists." },
          }),
        }),
      ),
    );
    render(
      <TestProviders>
        <ForensicReportPanel caseId={emptyCaseId} />
      </TestProviders>,
    );
    expect(
      await screen.findByText(/No forensic report yet/i, {}, { timeout: 5000 }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Generate Report/i })).toBeInTheDocument();
  });
});
