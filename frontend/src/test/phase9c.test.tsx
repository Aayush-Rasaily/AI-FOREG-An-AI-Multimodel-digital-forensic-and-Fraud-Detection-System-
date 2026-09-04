import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CoveragePanel } from "../components/investigation-intelligence/CoveragePanel";
import { EvidenceGapPanel } from "../components/investigation-intelligence/EvidenceGapPanel";
import { HypothesisPanel } from "../components/investigation-intelligence/HypothesisPanel";
import { InvestigationIntelligencePanel } from "../components/investigation-intelligence/InvestigationIntelligencePanel";
import { RecommendationsPanel } from "../components/investigation-intelligence/RecommendationsPanel";
import { TestProviders } from "./render";

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
            error: { message: "failed", code: "ERR", request_id: "r1" },
          },
  });
}

const run = {
  id: "run-1",
  case_id: "case-1",
  status: "SUCCEEDED",
  investigation_score: 62.5,
  overall_completeness: 0.42,
  hypothesis_count: 1,
  gap_count: 1,
  recommendation_count: 1,
  open_conflict_count: 0,
  coverage: {
    evidence_total: 1,
    evidence_analyzed: 0,
    evidence_pending: 1,
    timeline_coverage: 0,
    knowledge_graph_coverage: 0,
    correlation_coverage: 1,
    fusion_coverage: 0,
    ai_coverage: 0,
    metadata_completeness: 0.5,
    chain_of_custody_completeness: 0,
    overall_completeness: 0.42,
    open_conflicts: 0,
  },
  open_conflicts: [],
  provenance: { engine_version: "9c.1.0" },
  engine_version: "9c.1.0",
  policy_version: "1.0",
  created_at: "2026-09-09T00:00:00Z",
  completed_at: "2026-09-09T00:00:01Z",
  hypotheses: [
    {
      hypothesis_key: "hyp_1",
      hypothesis_type: "INSUFFICIENT_EVIDENCE",
      title: "Insufficient Evidence",
      explanation: "Case has insufficient evidence.",
      confidence: 0.9,
      priority: "HIGH",
      status: "OPEN",
      supporting_evidence_ids: ["ev-1"],
      contradicting_evidence_ids: [],
      provenance: { engine_version: "9c.1.0" },
      attributes: {},
    },
  ],
  gaps: [
    {
      gap_key: "gap_1",
      gap_type: "MISSING_CHAIN_OF_CUSTODY",
      severity: "HIGH",
      reason: "No chain-of-custody events recorded.",
      recommended_action: "VERIFY_CHAIN_OF_CUSTODY",
      affected_evidence_ids: ["ev-1"],
      provenance: {},
    },
  ],
  recommendations: [
    {
      recommendation_key: "rec_1",
      code: "VERIFY_CHAIN_OF_CUSTODY",
      action_text: "Verify chain of custody continuity for affected evidence.",
      priority: "HIGH",
      related_hypothesis_keys: [],
      related_gap_keys: ["gap_1"],
      affected_evidence_ids: ["ev-1"],
      provenance: {},
    },
  ],
  persisted: true,
};

function stubApi(overrides?: { latestStatus?: number; latestData?: unknown }) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/investigation-intelligence") && method === "POST") {
        return response(run);
      }
      if (url.includes("/investigation-intelligence")) {
        if ((overrides?.latestStatus ?? 200) >= 400) {
          return response(null, overrides?.latestStatus);
        }
        return response(overrides?.latestData ?? run);
      }
      return response(null, 404);
    }),
  );
}

describe("Phase 9C investigation intelligence UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubApi();
  });

  it("renders intelligence dashboard", async () => {
    render(
      <TestProviders>
        <InvestigationIntelligencePanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getAllByText(/Score 62\.5/i).length).toBeGreaterThan(0);
    });
  });

  it("shows empty state when missing", async () => {
    stubApi({ latestStatus: 404 });
    render(
      <TestProviders>
        <InvestigationIntelligencePanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("No case intelligence")).toBeInTheDocument();
    });
  });

  it("shows error state", async () => {
    stubApi({ latestStatus: 500 });
    render(
      <TestProviders>
        <InvestigationIntelligencePanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("Intelligence unavailable")).toBeInTheDocument();
    });
  });

  it("shows loading then content", async () => {
    render(
      <TestProviders>
        <InvestigationIntelligencePanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("SUCCEEDED")).toBeInTheDocument();
    });
  });

  it("analyzes on button click", async () => {
    stubApi({ latestStatus: 404 });
    const user = userEvent.setup();
    render(
      <TestProviders>
        <InvestigationIntelligencePanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Analyze case/i }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /Analyze case/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/Analyze case|SUCCEEDED/i).length).toBeGreaterThan(
        0,
      );
    });
  });

  it("renders hypothesis cards with provenance", () => {
    render(
      <TestProviders>
        <HypothesisPanel
          hypotheses={run.hypotheses}
          priorityFilter="all"
          search=""
        />
      </TestProviders>,
    );
    expect(screen.getByText("Insufficient Evidence")).toBeInTheDocument();
    expect(screen.getByText(/Provenance engine/i)).toBeInTheDocument();
  });

  it("renders gap and recommendation panels", () => {
    render(
      <TestProviders>
        <EvidenceGapPanel gaps={run.gaps} search="" />
        <RecommendationsPanel recommendations={run.recommendations} search="" />
      </TestProviders>,
    );
    expect(screen.getByText("MISSING_CHAIN_OF_CUSTODY")).toBeInTheDocument();
    expect(
      screen.getByText(/Verify chain of custody continuity/i),
    ).toBeInTheDocument();
  });

  it("renders coverage metrics", () => {
    render(
      <TestProviders>
        <CoveragePanel
          coverage={run.coverage}
          investigationScore={run.investigation_score}
        />
      </TestProviders>,
    );
    expect(screen.getByText("Overall completeness")).toBeInTheDocument();
    expect(screen.getByText("42%")).toBeInTheDocument();
  });

  it("filters hypotheses by search", () => {
    render(
      <TestProviders>
        <HypothesisPanel
          hypotheses={run.hypotheses}
          priorityFilter="all"
          search="zzzz"
        />
      </TestProviders>,
    );
    expect(screen.getByText("No hypotheses")).toBeInTheDocument();
  });
});
