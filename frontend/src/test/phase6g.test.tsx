import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CaseIntelligencePanel } from "../components/investigation/CaseIntelligencePanel";
import { CaseTimelinePanel } from "../components/investigation/CaseTimelinePanel";
import { TestProviders } from "./render";

const caseId = "00000000-0000-0000-0000-000000000401";

const caseDetail = {
  id: "00000000-0000-0000-0000-000000000402",
  case_id: caseId,
  status: "SUCCEEDED",
  engine_version: "1.0",
  policy_version: "1.0",
  verdict: "suspicious",
  risk_score: 78,
  confidence: 0.86,
  evidence_count: 2,
  conflicts_count: 1,
  relationships_count: 1,
  created_at: "2026-08-31T00:00:00Z",
  started_at: "2026-08-31T00:00:00Z",
  completed_at: "2026-08-31T00:00:01Z",
  error_code: null,
  error_message: null,
  metadata: {},
  provenance: { case_id: caseId },
  coverage: {
    total_evidence: 2,
    analyzed: 1,
    not_analyzed: 1,
    inconclusive: 0,
    insufficient_evidence: 0,
    unavailable: 0,
    failed: 0,
    supporting_evidence: 1,
    contradictory_evidence: 0,
    open_conflicts: 1,
    supported_modalities: ["forensics"],
  },
  participations: [
    {
      evidence_id: "00000000-0000-0000-0000-000000000403",
      evidence_number: "EVID-001",
      evidence_type: "document",
      evidence_hash: "a".repeat(64),
      evidence_status: "ANALYZED",
      coverage_status: "analyzed",
      fusion_run_id: "00000000-0000-0000-0000-000000000404",
      fusion_verdict: "suspicious",
      risk_score: 70,
      confidence: 0.8,
      supporting_finding_ids: [],
      contradictory_finding_ids: [],
      conflicts_count: 0,
      participating_modalities: ["forensics"],
      unavailable_modalities: [],
      fusion_engine_version: "1.0",
      fusion_policy_version: "1.0",
      fusion_completed_at: "2026-08-31T00:00:01Z",
    },
    {
      evidence_id: "00000000-0000-0000-0000-000000000405",
      evidence_number: "EVID-002",
      evidence_type: "image",
      evidence_hash: "b".repeat(64),
      evidence_status: "READY_FOR_ANALYSIS",
      coverage_status: "not_analyzed",
      fusion_run_id: null,
      fusion_verdict: null,
      risk_score: null,
      confidence: null,
      supporting_finding_ids: [],
      contradictory_finding_ids: [],
      conflicts_count: 0,
      participating_modalities: [],
      unavailable_modalities: [],
      fusion_engine_version: null,
      fusion_policy_version: null,
      fusion_completed_at: null,
      reason: "No Phase 6F fusion analysis exists for this evidence.",
    },
  ],
  relationships: [
    {
      relationship_id: "comparison:1",
      evidence_a_id: "00000000-0000-0000-0000-000000000403",
      evidence_b_id: "00000000-0000-0000-0000-000000000405",
      relationship_type: "comparison_link",
      confidence: 1,
      supporting_reason: "Existing comparison run links questioned and reference evidence.",
      source_reference: "comparison_run:1",
      status: "confirmed",
    },
  ],
  conflicts: [
    {
      conflict_id: "verdict:1",
      conflict_type: "verdict_disagreement",
      severity: "HIGH",
      involved_evidence_ids: ["00000000-0000-0000-0000-000000000403"],
      involved_finding_ids: [],
      explanation: "Evidence items disagree on suspicious versus genuine fusion verdicts.",
      resolution_status: "open",
    },
  ],
  timeline: [
    {
      event_id: "registered:1",
      event_type: "evidence_registered",
      timestamp: "2026-08-31T00:00:00Z",
      timestamp_known: true,
      evidence_id: "00000000-0000-0000-0000-000000000403",
      source_reference: "evidence:1",
      description: "Evidence EVID-001 registered.",
    },
  ],
  explanation: "Case verdict: suspicious.",
  limitations: "Case synthesis aggregates Phase 6F fusion results.",
  supporting_evidence_ids: ["00000000-0000-0000-0000-000000000403"],
  contradictory_evidence_ids: [],
};

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
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
      if (url.includes("/intelligence/latest")) {
        return response(caseDetail);
      }
      if (url.includes("/timeline")) {
        return response(caseDetail.timeline);
      }
      return response({});
    }),
  );
});

describe("CaseIntelligencePanel", () => {
  it("renders case verdict, coverage, and evidence states", async () => {
    render(
      <TestProviders>
        <CaseIntelligencePanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("EVID-001")).toBeInTheDocument();
    expect(screen.getAllByText("suspicious").length).toBeGreaterThan(0);
    expect(screen.getByText(/Case risk: 78/)).toBeInTheDocument();
    expect(screen.getByText("EVID-002")).toBeInTheDocument();
    expect(screen.getAllByText(/not analyzed/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/comparison link/i)).toBeInTheDocument();
    expect(screen.getByText(/verdict disagreement/i)).toBeInTheDocument();
  });
});

describe("CaseTimelinePanel", () => {
  it("renders timeline events and unknown timestamp handling", async () => {
    render(
      <TestProviders>
        <CaseTimelinePanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText(/Evidence EVID-001 registered/i)).toBeInTheDocument();
    expect(screen.getByText(/evidence registered/i)).toBeInTheDocument();
  });
});
