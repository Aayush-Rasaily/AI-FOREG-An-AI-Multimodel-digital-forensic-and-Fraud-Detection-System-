import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardPage } from "../pages/DashboardPage";
import { TestProviders } from "./render";

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () =>
      status >= 200 && status < 300
        ? { success: true, data, request_id: "r1", timestamp: "2026-09-09T00:00:00Z" }
        : {
            success: false,
            error: { message: "failed", code: "ERR", request_id: "r1" },
          },
  });
}

const caseItem = {
  id: "case-1",
  case_number: "CASE-1001",
  title: "Wire transfer anomaly",
  description: null,
  status: "IN_PROGRESS",
  priority: "HIGH",
  created_at: "2026-09-01T00:00:00Z",
  updated_at: "2026-09-09T12:00:00Z",
};

const analyticsRun = {
  id: "an-1",
  status: "SUCCEEDED",
  metric_count: 3,
  metrics: [
    {
      key: "evidence_count",
      label: "Evidence Count",
      value: 12,
      unit: "count",
      category: "evidence",
      provenance: {},
    },
    {
      key: "fusion_runs",
      label: "Fusion Runs",
      value: 2,
      unit: "count",
      category: "ai",
      provenance: {},
    },
  ],
  sections: {
    cases: { opened: 2, completed: 1, reports_generated: 1 },
    evidence: { processed: 12 },
    ai: {
      analyses_completed: 4,
      breakdown: { image: 5, document: 4, video: 2, audio: 1 },
      fusion_runs: 2,
      correlations: 3,
      average_confidence: 0.82,
    },
    integrity: { alerts: 2 },
  },
  trends: {
    cases_opened: [
      { index: 0, label: "t0", value: 1 },
      { index: 1, label: "current", value: 2 },
    ],
  },
  dashboard: { title: "Investigation Analytics" },
  provenance: {},
  engine_version: "11d.1.0",
  policy_version: "1.0",
  created_at: "2026-09-09T00:00:00Z",
  completed_at: "2026-09-09T00:00:01Z",
  persisted: true,
};

const health = {
  status: "healthy",
  version: "1.0.0",
  environment: "test",
  database: "healthy",
  timestamp: "2026-09-09T00:00:00Z",
};

const metrics = {
  evidence_count: 12,
  case_count: 2,
  report_count: 1,
  timeline_count: 1,
  fusion_run_count: 2,
  entity_graph_count: 0,
  correlation_count: 3,
  ai_analysis_count: 4,
  processing_job_count: 2,
  average_processing_time_ms: 120,
  failure_rate: 0,
  storage_growth_bytes: null,
};

const jobs = {
  categories: {},
  totals: { queued: 1, running: 1, completed: 8, failed: 0, cancelled: 0 },
  active_analyses: 1,
  queue_length: 1,
  category_list: [],
};

function stubApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/cases")) {
        return response({
          items: [caseItem],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      if (url.includes("/analytics")) {
        return response(analyticsRun);
      }
      if (url.endsWith("/health") || url.includes("/health?")) {
        return response(health);
      }
      if (url.includes("/system/metrics")) {
        return response(metrics);
      }
      if (url.includes("/system/jobs")) {
        return response(jobs);
      }
      return response({}, 404);
    }),
  );
}

describe("phase 11d executive dashboard", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    stubApi();
  });

  it("renders KPI cards, risk heatmap, and recent case open control", async () => {
    render(
      <TestProviders>
        <DashboardPage />
      </TestProviders>,
    );

    expect(
      await screen.findByRole("heading", { name: "Investigation dashboard" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByLabelText("Key performance indicators")).toBeInTheDocument();
    });

    expect(screen.getByText("Open cases")).toBeInTheDocument();
    expect(screen.getByText("Evidence items")).toBeInTheDocument();
    expect(screen.getByText("Fusion runs")).toBeInTheDocument();

    expect(
      await screen.findByRole("heading", { name: "Risk heatmap" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Risk heatmap")).toBeInTheDocument();

    expect(
      await screen.findByRole("button", { name: "Open CASE-1001" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Wire transfer anomaly/).length).toBeGreaterThan(
      0,
    );
  });

  it("shows processing queue progressbars and activity feed", async () => {
    render(
      <TestProviders>
        <DashboardPage />
      </TestProviders>,
    );

    expect(
      await screen.findByRole("heading", { name: "Processing status" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByLabelText("Running 1")).toBeInTheDocument();
      expect(screen.getByLabelText("Queued 1")).toBeInTheDocument();
    });

    expect(
      await screen.findByLabelText("Activity feed"),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/CASE-1001/).length).toBeGreaterThan(0);
  });
});
