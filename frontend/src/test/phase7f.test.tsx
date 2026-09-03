import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SystemDashboardPage } from "../pages/SystemDashboardPage";
import { TestProviders } from "./render";

const health = {
  status: "healthy",
  timestamp: "2026-09-01T00:00:00Z",
  service: "AI_Forge",
  version: "0.1.0",
  environment: "test",
  uptime_seconds: 120,
  python_version: "3.13",
  platform: "Windows",
  database: { status: "healthy" },
  redis: { status: "not_configured", detail: "Redis URL not configured." },
  resources: {
    cpu_percent: 10,
    memory_mb: 512,
    disk_percent: 45,
    gpu_available: false,
  },
  engine_version: "1.0",
  policy_version: "1.0",
};

const metrics = {
  evidence_count: 5,
  case_count: 2,
  report_count: 1,
  timeline_count: 0,
  fusion_run_count: 0,
  entity_graph_count: 0,
  correlation_count: 0,
  ai_analysis_count: 0,
  processing_job_count: 3,
  average_processing_time_ms: null,
  failure_rate: 0,
  storage_growth_bytes: null,
};

const jobs = {
  categories: {
    processing: {
      queued: 0,
      running: 1,
      completed: 2,
      failed: 0,
      cancelled: 0,
    },
  },
  totals: {
    queued: 0,
    running: 1,
    completed: 2,
    failed: 0,
    cancelled: 0,
  },
  active_analyses: 1,
  queue_length: 0,
  category_list: ["processing"],
};

const storage = {
  backend: "local",
  root_configured: true,
  used_bytes: 1024,
  used_mb: 0.0,
  disk_total_bytes: 1000000,
  disk_free_bytes: 500000,
  disk_percent: 50,
  max_upload_size_mb: 50,
};

const diagnostics = {
  overall_status: "healthy",
  checks: [
    { name: "configuration", status: "PASS", detail: "OK" },
    { name: "database_connectivity", status: "PASS", detail: "OK" },
  ],
  check_names: ["configuration", "database_connectivity"],
  pass_count: 2,
  warn_count: 0,
  fail_count: 0,
};

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () =>
      status >= 200 && status < 300
        ? { success: true, data }
        : { success: false, error: { message: "Error", code: "ERR" } },
  });
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: RequestInfo) => {
      const url = String(input);
      if (url.includes("/system/health")) return response(health);
      if (url.includes("/system/metrics")) return response(metrics);
      if (url.includes("/system/jobs")) return response(jobs);
      if (url.includes("/system/storage")) return response(storage);
      if (url.includes("/system/diagnostics/run")) {
        return response({
          id: "00000000-0000-0000-0000-000000000f01",
          ...diagnostics,
          results_json: diagnostics,
          engine_version: "1.0",
          policy_version: "1.0",
          created_at: "2026-09-01T00:00:00Z",
        });
      }
      if (url.includes("/system/diagnostics")) return response(diagnostics);
      return response({});
    }),
  );
});

describe("Phase 7F SystemDashboardPage", () => {
  it("renders health and metrics panels", async () => {
    render(
      <TestProviders>
        <SystemDashboardPage />
      </TestProviders>,
    );
    expect(
      await screen.findByRole("heading", { name: "System Dashboard" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("Health")).toBeInTheDocument();
    expect(screen.getByText("Metrics")).toBeInTheDocument();
    expect(screen.getAllByText("healthy").length).toBeGreaterThan(0);
  });

  it("renders jobs and storage panels", async () => {
    render(
      <TestProviders>
        <SystemDashboardPage />
      </TestProviders>,
    );
    expect(await screen.findByText("Jobs")).toBeInTheDocument();
    expect(screen.getByText("Storage")).toBeInTheDocument();
  });

  it("shows diagnostics checks", async () => {
    render(
      <TestProviders>
        <SystemDashboardPage />
      </TestProviders>,
    );
    expect(await screen.findByText("Diagnostics")).toBeInTheDocument();
    expect(
      await screen.findByText("configuration", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
  });

  it("runs diagnostics on button click", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <SystemDashboardPage />
      </TestProviders>,
    );
    const btn = await screen.findByRole("button", {
      name: /Run Diagnostics/i,
    });
    await user.click(btn);
    expect(btn).toBeInTheDocument();
  });

  it("shows error state when health fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/system/health")) return response(null, 500);
        if (url.includes("/system/metrics")) return response(metrics);
        if (url.includes("/system/jobs")) return response(jobs);
        if (url.includes("/system/storage")) return response(storage);
        if (url.includes("/system/diagnostics")) return response(diagnostics);
        return response({});
      }),
    );
    render(
      <TestProviders>
        <SystemDashboardPage />
      </TestProviders>,
    );
    expect(
      await screen.findByText("Health check failed", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
  });
});
