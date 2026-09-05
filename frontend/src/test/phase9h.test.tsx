import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CompatibilityPanel } from "../components/platform-validation/CompatibilityPanel";
import { HealthReportPanel } from "../components/platform-validation/HealthReportPanel";
import { IssueViewer } from "../components/platform-validation/IssueViewer";
import { PlatformReadinessDashboard } from "../components/platform-validation/PlatformReadinessDashboard";
import { ReadinessSummary } from "../components/platform-validation/ReadinessSummary";
import { ValidationResults } from "../components/platform-validation/ValidationResults";
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
  id: "pv-1",
  status: "SUCCEEDED",
  readiness_score: 100,
  readiness_level: "READY",
  check_count: 2,
  pass_count: 2,
  warn_count: 0,
  fail_count: 0,
  results: [
    {
      check_key: "migrations",
      category: "migrations",
      label: "Database migrations",
      status: "PASS",
      message: "ok",
      details: {},
    },
    {
      check_key: "api_compatibility",
      category: "api",
      label: "API compatibility",
      status: "PASS",
      message: "ok",
      details: {},
    },
  ],
  issues: [],
  health_report: {
    counts: { pass: 2, warn: 0, fail: 0, total: 2 },
    categories: { migrations: [{}], api: [{}] },
    ai_rerun: false,
    data_mutation: false,
  },
  compatibility: {
    modules: { analytics: "9g.1.0", platform_validation: "9h.1.0" },
    ai_rerun: false,
    forecasting: false,
  },
  provenance: { deterministic: true },
  engine_version: "9h.1.0",
  policy_version: "1.0",
  created_at: "2026-09-14T00:00:00Z",
  completed_at: "2026-09-14T00:00:01Z",
  persisted: true,
};

function stubApi(overrides?: { status?: number }) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/platform/validate") && method === "POST") {
        return response(run);
      }
      if (url.includes("/platform/validation/latest")) {
        if ((overrides?.status ?? 200) >= 400) {
          return response(null, overrides?.status);
        }
        return response(run);
      }
      if (url.includes("/platform/readiness")) {
        return response({
          readiness_score: 100,
          readiness_level: "READY",
          check_count: 2,
          pass_count: 2,
          warn_count: 0,
          fail_count: 0,
          engine_version: "9h.1.0",
          policy_version: "1.0",
          persisted: true,
          run_id: "pv-1",
        });
      }
      if (url.includes("/platform/health/report")) {
        return response({
          report: run.health_report,
          engine_version: "9h.1.0",
          policy_version: "1.0",
          persisted: true,
          run_id: "pv-1",
        });
      }
      return response(null, 404);
    }),
  );
}

describe("Phase 9H platform validation UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubApi();
  });

  it("renders platform readiness dashboard", async () => {
    render(
      <TestProviders>
        <PlatformReadinessDashboard />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getAllByText("SUCCEEDED").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Platform Health")).toBeInTheDocument();
    expect(screen.getByText("READY")).toBeInTheDocument();
  });

  it("shows error state", async () => {
    stubApi({ status: 500 });
    render(
      <TestProviders>
        <PlatformReadinessDashboard />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("Validation unavailable")).toBeInTheDocument();
    });
  });

  it("runs validation on click", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <PlatformReadinessDashboard />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("Run validation")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Run validation"));
    await waitFor(() => {
      expect(screen.getAllByText("SUCCEEDED").length).toBeGreaterThan(0);
    });
  });

  it("renders empty readiness summary", () => {
    render(
      <TestProviders>
        <ReadinessSummary run={null} />
      </TestProviders>,
    );
    expect(screen.getByText("No validation results yet.")).toBeInTheDocument();
  });

  it("renders validation results", () => {
    render(
      <TestProviders>
        <ValidationResults results={run.results} />
      </TestProviders>,
    );
    expect(screen.getByText("Database migrations")).toBeInTheDocument();
  });

  it("renders empty issue viewer", () => {
    render(
      <TestProviders>
        <IssueViewer issues={[]} />
      </TestProviders>,
    );
    expect(screen.getByText("No issues reported.")).toBeInTheDocument();
  });

  it("renders issues", () => {
    render(
      <TestProviders>
        <IssueViewer
          issues={[
            {
              check_key: "migrations",
              category: "migrations",
              severity: "FAIL",
              message: "broken",
              details: {},
            },
          ]}
        />
      </TestProviders>,
    );
    expect(screen.getByText("broken")).toBeInTheDocument();
  });

  it("renders health report", () => {
    render(
      <TestProviders>
        <HealthReportPanel report={run.health_report} />
      </TestProviders>,
    );
    expect(screen.getByText(/Total · 2/)).toBeInTheDocument();
  });

  it("renders empty health report", () => {
    render(
      <TestProviders>
        <HealthReportPanel report={{}} />
      </TestProviders>,
    );
    expect(screen.getByText("No health report yet.")).toBeInTheDocument();
  });

  it("renders compatibility panel", () => {
    render(
      <TestProviders>
        <CompatibilityPanel compatibility={run.compatibility} />
      </TestProviders>,
    );
    expect(screen.getByText("analytics")).toBeInTheDocument();
    expect(screen.getByText("9g.1.0")).toBeInTheDocument();
  });
});
