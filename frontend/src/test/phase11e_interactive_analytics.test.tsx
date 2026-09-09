import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { InteractiveBarChart } from "../components/viz/InteractiveBarChart";
import { InteractiveTimelineViz } from "../components/viz/InteractiveTimelineViz";
import { RelationshipGraph } from "../components/viz/RelationshipGraph";
import { AnalyticsDashboard } from "../components/analytics/AnalyticsDashboard";
import { TestProviders } from "./render";
import type { TimelineEvent } from "../types/timeline";

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () =>
      status >= 200 && status < 300
        ? {
            success: true,
            data,
            request_id: "r1",
            timestamp: "2026-09-10T00:00:00Z",
          }
        : {
            success: false,
            error: { message: "failed", code: "ERR", request_id: "r1" },
          },
  });
}

const analyticsRun = {
  id: "an-11e",
  status: "SUCCEEDED",
  metric_count: 2,
  metrics: [
    {
      key: "cases_opened",
      label: "Cases Opened",
      value: 3,
      unit: "count",
      category: "cases",
      provenance: {},
    },
  ],
  sections: {
    overview: {
      kpis: [
        {
          key: "cases_opened",
          label: "Cases Opened",
          value: 3,
          unit: "count",
        },
      ],
    },
    cases: { opened: 3, completed: 1, reports_generated: 1 },
    evidence: { processed: 5 },
    ai: {
      analyses_completed: 4,
      breakdown: { image: 2, document: 3 },
      fusion_runs: 1,
      correlations: 2,
    },
    workflow: { workflow_completion_pct: 0.5 },
    integrity: { alerts: 1, runs: 2 },
  },
  trends: {
    cases_opened: [
      { index: 0, label: "t0", value: 1 },
      { index: 1, label: "current", value: 3 },
    ],
  },
  dashboard: { title: "Investigation Analytics" },
  provenance: { forecasting: false },
  engine_version: "9g.1.0",
  policy_version: "1.0",
  created_at: "2026-09-10T00:00:00Z",
  completed_at: "2026-09-10T00:00:01Z",
  persisted: true,
};

const caseItem = {
  id: "case-1",
  case_number: "CASE-11E",
  title: "Viz case",
  description: null,
  status: "OPEN",
  priority: "HIGH",
  created_at: "2026-09-01T00:00:00Z",
  updated_at: "2026-09-10T12:00:00Z",
};

function stubApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/analytics/refresh") && method === "POST") {
        return response(analyticsRun);
      }
      if (url.includes("/analytics/export")) {
        return response({
          format: "json",
          generated_at: "2026-09-10T00:00:00Z",
          engine_version: "9g.1.0",
          policy_version: "1.0",
          payload: analyticsRun,
        });
      }
      if (url.includes("/analytics")) {
        return response(analyticsRun);
      }
      if (url.includes("/cases")) {
        return response({
          items: [caseItem],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      if (url.includes("/system/metrics")) {
        return response({
          evidence_count: 5,
          case_count: 1,
          report_count: 1,
          timeline_count: 1,
          fusion_run_count: 1,
          entity_graph_count: 0,
          correlation_count: 2,
          ai_analysis_count: 4,
          processing_job_count: 1,
          average_processing_time_ms: 10,
          failure_rate: 0,
          storage_growth_bytes: null,
        });
      }
      if (url.includes("/system/jobs")) {
        return response({
          categories: {},
          totals: {
            queued: 1,
            running: 0,
            completed: 4,
            failed: 0,
            cancelled: 0,
          },
          active_analyses: 0,
          queue_length: 1,
          category_list: [],
        });
      }
      return response({}, 404);
    }),
  );
}

const sampleEvents: TimelineEvent[] = [
  {
    id: "1",
    timeline_id: "t1",
    case_id: "case-1",
    evidence_id: "e1",
    event_id: "ev1",
    event_type: "evidence_uploaded",
    timestamp: "2026-09-01T00:00:00Z",
    timezone: "UTC",
    normalized_timestamp: "2026-09-01T00:00:00Z",
    confidence: 0.9,
    uncertainty_ms: 0,
    description: "Evidence uploaded",
    source: "evidence",
    source_id: "e1",
    provenance: {},
    metadata: {},
    supporting_artifacts: [],
    created_at: "2026-09-01T00:00:00Z",
  },
  {
    id: "2",
    timeline_id: "t1",
    case_id: "case-1",
    evidence_id: null,
    event_id: "ev2",
    event_type: "fusion_completed",
    timestamp: "2026-09-02T00:00:00Z",
    timezone: "UTC",
    normalized_timestamp: "2026-09-02T00:00:00Z",
    confidence: 0.8,
    uncertainty_ms: 0,
    description: "Fusion completed",
    source: "fusion",
    source_id: "f1",
    provenance: {},
    metadata: {},
    supporting_artifacts: [],
    created_at: "2026-09-02T00:00:00Z",
  },
];

describe("phase 11e interactive analytics", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    stubApi();
  });

  it("renders interactive charts with export controls", () => {
    const onSelect = vi.fn();
    render(
      <TestProviders>
        <InteractiveBarChart
          onSelect={onSelect}
          slices={[
            { id: "a", label: "Image", value: 3, tone: "primary" },
            { id: "b", label: "Document", value: 5, tone: "info" },
          ]}
          title="Evidence types"
        />
      </TestProviders>,
    );
    expect(screen.getByRole("img", { name: "Evidence types" })).toBeInTheDocument();
    expect(screen.getByLabelText("Export Evidence types as SVG")).toBeInTheDocument();
    expect(screen.getByLabelText("Export Evidence types as PNG")).toBeInTheDocument();
    expect(screen.getByLabelText("Evidence types legend")).toBeInTheDocument();
  });

  it("supports click-to-filter on chart legend", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <TestProviders>
        <InteractiveBarChart
          onSelect={onSelect}
          slices={[{ id: "image", label: "Image", value: 2 }]}
          title="Evidence types"
        />
      </TestProviders>,
    );
    await user.click(screen.getByRole("button", { name: /Image \(2\)/i }));
    expect(onSelect).toHaveBeenCalled();
  });

  it("renders relationship graph with search and legend", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <RelationshipGraph
          edges={[{ id: "e1", source: "c1", target: "ev1" }]}
          nodes={[
            { id: "c1", label: "CASE-1", kind: "case", detail: "Open" },
            { id: "ev1", label: "image", kind: "evidence" },
          ]}
        />
      </TestProviders>,
    );
    expect(screen.getByLabelText("Search graph nodes")).toBeInTheDocument();
    expect(screen.getByLabelText("Graph legend")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Search graph nodes"), "CASE");
    expect(screen.getByRole("img", { name: /relationship graph/i })).toBeInTheDocument();
  });

  it("renders interactive timeline visualization", () => {
    render(
      <TestProviders>
        <InteractiveTimelineViz events={sampleEvents} />
      </TestProviders>,
    );
    expect(screen.getByRole("img", { name: "Interactive timeline" })).toBeInTheDocument();
    expect(screen.getByLabelText("Export timeline SVG")).toBeInTheDocument();
    expect(screen.getByText(/evidence \(1\)/i)).toBeInTheDocument();
    expect(screen.getByText(/fusion \(1\)/i)).toBeInTheDocument();
  });

  it("loads interactive workspace inside analytics dashboard", async () => {
    render(
      <TestProviders>
        <AnalyticsDashboard />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("Investigation Analytics")).toBeInTheDocument();
    });
    expect(
      await screen.findByText("Interactive filters", {}, { timeout: 10_000 }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Evidence types" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Risk heatmap" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", {
        name: "Evidence relationship graph",
      }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Top risks" }),
    ).toBeInTheDocument();
  });
});
