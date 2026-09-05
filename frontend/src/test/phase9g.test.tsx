import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AnalyticsDashboard } from "../components/analytics/AnalyticsDashboard";
import { ExportPanel } from "../components/analytics/ExportPanel";
import { KpiCards } from "../components/analytics/KpiCards";
import { SectionMetrics } from "../components/analytics/SectionMetrics";
import { TrendCharts } from "../components/analytics/TrendCharts";
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
  id: "an-1",
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
    cases: { opened: 3, completed: 1, in_progress: 2, reports_generated: 0 },
    evidence: { processed: 5 },
    ai: { analyses_completed: 4, breakdown: { image: 2 } },
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
  created_at: "2026-09-13T00:00:00Z",
  completed_at: "2026-09-13T00:00:01Z",
  persisted: true,
};

function stubApi(overrides?: { status?: number }) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/analytics/refresh") && method === "POST") {
        return response(run);
      }
      if (url.includes("/analytics/export")) {
        return response({
          format: "json",
          generated_at: "2026-09-13T00:00:02Z",
          engine_version: "9g.1.0",
          policy_version: "1.0",
          payload: { metrics: run.metrics },
        });
      }
      if (url.includes("/analytics")) {
        if ((overrides?.status ?? 200) >= 400) {
          return response(null, overrides?.status);
        }
        return response(run);
      }
      return response(null, 404);
    }),
  );
}

describe("Phase 9G analytics UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubApi();
  });

  it("renders analytics dashboard", async () => {
    render(
      <TestProviders>
        <AnalyticsDashboard />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getAllByText("SUCCEEDED").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Investigation Analytics")).toBeInTheDocument();
  });

  it("shows error state", async () => {
    stubApi({ status: 500 });
    render(
      <TestProviders>
        <AnalyticsDashboard />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("Analytics unavailable")).toBeInTheDocument();
    });
  });

  it("refreshes analytics", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <AnalyticsDashboard />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Refresh analytics/i }),
      ).toBeInTheDocument();
    });
    await user.click(
      screen.getByRole("button", { name: /Refresh analytics/i }),
    );
  });

  it("renders kpi cards", () => {
    render(
      <TestProviders>
        <KpiCards items={run.sections.overview.kpis} />
      </TestProviders>,
    );
    expect(screen.getByText("Cases Opened")).toBeInTheDocument();
  });

  it("renders trend charts", () => {
    render(
      <TestProviders>
        <TrendCharts trends={run.trends} />
      </TestProviders>,
    );
    expect(screen.getByText("cases_opened")).toBeInTheDocument();
  });

  it("renders case metrics", () => {
    render(
      <TestProviders>
        <SectionMetrics
          data={run.sections.cases}
          description="cases"
          title="Case Metrics"
        />
      </TestProviders>,
    );
    expect(screen.getByText("Case Metrics")).toBeInTheDocument();
  });

  it("renders ai metrics", () => {
    render(
      <TestProviders>
        <SectionMetrics
          data={run.sections.ai}
          description="ai"
          title="AI Usage Metrics"
        />
      </TestProviders>,
    );
    expect(screen.getByText("AI Usage Metrics")).toBeInTheDocument();
  });

  it("renders workflow metrics", () => {
    render(
      <TestProviders>
        <SectionMetrics
          data={run.sections.workflow}
          description="workflow"
          title="Workflow Metrics"
        />
      </TestProviders>,
    );
    expect(screen.getByText("Workflow Metrics")).toBeInTheDocument();
  });

  it("renders export panel", async () => {
    const user = userEvent.setup();
    const onExport = vi.fn();
    render(
      <TestProviders>
        <ExportPanel onExport={onExport} />
      </TestProviders>,
    );
    await user.click(screen.getByRole("button", { name: /Export JSON/i }));
    expect(onExport).toHaveBeenCalled();
  });

  it("shows provenance", async () => {
    render(
      <TestProviders>
        <AnalyticsDashboard />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(
        screen.getByText(/Provenance · engine 9g.1.0/),
      ).toBeInTheDocument();
    });
  });
});
