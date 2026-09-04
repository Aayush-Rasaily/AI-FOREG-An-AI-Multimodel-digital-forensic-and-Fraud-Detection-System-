import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MonitoringDashboard } from "../components/monitoring/MonitoringDashboard";
import { SystemHealthCard } from "../components/monitoring/SystemHealthCard";
import { TestProviders } from "./render";

const dashboard = {
  system_health: {
    status: "HEALTHY",
    reasons: ["All monitored indicators within healthy thresholds."],
    signals: { processing_failure_rate: 0 },
    assessed_at: "2026-09-04T00:00:00Z",
    engine_version: "8d.1.0",
    policy_version: "8d.1.0",
  },
  processing: {
    jobs_created: 3,
    jobs_completed: 2,
    failures: 1,
    retries: 0,
    execution_duration_avg_ms: 12.5,
    execution_duration_p95_ms: 20,
    success_rate: 0.6667,
    failure_rate: 0.3333,
  },
  ai: {
    model_executions: 1,
    total_failures: 0,
    total_unavailable: 0,
    modalities: [{ modality: "image", executions: 1, failures: 0 }],
    detector_failure_rankings: [
      { modality: "image", failures: 0, failure_rate: 0 },
    ],
  },
  cases: {
    cases_created: 1,
    evidence_uploaded: 2,
    timelines_created: 0,
    correlation_runs: 0,
  },
  reports: { reports_generated: 0, average_generation_ms: null },
  api: {
    request_counts: 4,
    source: "audit_events",
    endpoint_usage: [{ operation: "case.create", count: 1 }],
  },
  activity: {
    recent_events: [
      {
        id: "e1",
        operation: "case.create",
        user: "admin",
        timestamp: "2026-09-04T00:00:00Z",
      },
    ],
  },
  bottlenecks: { inactive_investigations: [] },
  audit_summary: {
    busiest_investigators: [{ user: "admin", event_count: 2 }],
    inactive_investigations: [],
  },
  kpis: { average_processing_time_ms: 12.5 },
  trends: { cases_created: 1 },
  recent_failures: [],
  generated_at: "2026-09-04T00:00:00Z",
  engine_version: "8d.1.0",
  policy_version: "8d.1.0",
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
              message: "Error",
              code: "API_ERROR",
              request_id: null,
            },
          },
  });
}

describe("Phase 8D monitoring frontend", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/monitoring/dashboard")) {
          return response(dashboard);
        }
        return response({});
      }),
    );
  });

  it("renders health badge and metric panels", async () => {
    render(
      <TestProviders>
        <MonitoringDashboard />
      </TestProviders>,
    );
    expect(
      await screen.findByText("Monitoring Dashboard"),
    ).toBeInTheDocument();
    expect(await screen.findByText(/Health: HEALTHY/i)).toBeInTheDocument();
    expect(await screen.findByText("Processing Summary")).toBeInTheDocument();
    expect(await screen.findByText("AI Summary")).toBeInTheDocument();
    expect(await screen.findByText("API Usage")).toBeInTheDocument();
    expect(screen.getAllByText("case.create").length).toBeGreaterThan(0);
  });

  it("renders system health card", () => {
    render(
      <SystemHealthCard
        reasons={["All monitored indicators within healthy thresholds."]}
        status="WARNING"
      />,
    );
    expect(screen.getByText(/Health: WARNING/i)).toBeInTheDocument();
  });

  it("renders loading state", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => new Promise(() => undefined)),
    );
    render(
      <TestProviders>
        <MonitoringDashboard />
      </TestProviders>,
    );
    expect(
      screen.getByText(/Loading operational monitoring/i),
    ).toBeInTheDocument();
  });
});
