import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ConfigurationPanel } from "../components/deployment/ConfigurationPanel";
import { DeploymentPanel } from "../components/deployment/DeploymentPanel";
import { HealthOverview } from "../components/deployment/HealthOverview";
import { ReleasePanel } from "../components/deployment/ReleasePanel";
import { SystemStatusPage } from "../pages/SystemStatusPage";
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

const version = {
  application_version: "0.1.0",
  service: "AI_Forge",
  environment: "local",
  policy_version: "1.0",
  engine_version: "8g.1.0",
};

const release = {
  application_version: "0.1.0",
  schema_version: "20260906_0025",
  migration_version: "20260906_0025",
  environment: "local",
  policy_versions: { deployment_policy: "1.0" },
  ai_engine_versions: { ai: "registered" },
  build_metadata: { deployment_engine: "8g.1.0" },
  git_commit: "abc123",
};

const liveness = {
  status: "alive",
  service: "AI_Forge",
  version: "0.1.0",
  timestamp: "2026-09-04T00:00:00Z",
  policy_version: "1.0",
  engine_version: "8g.1.0",
};

const readiness = {
  status: "ready",
  ready: true,
  validation_status: "DEGRADED",
  checks: [
    {
      check: "database",
      status: "PASS",
      message: "Database connectivity confirmed.",
    },
  ],
  timestamp: "2026-09-04T00:00:00Z",
  policy_version: "1.0",
  engine_version: "8g.1.0",
};

const startup = {
  status: "PASSED",
  checks: [],
  fail_count: 0,
  timestamp: "2026-09-04T00:00:00Z",
  environment: "local",
  version: "0.1.0",
  policy_version: "1.0",
  engine_version: "8g.1.0",
  graceful_shutdown_supported: true,
};

const configuration = {
  profile: {
    profile: "local",
    version: "0.1.0",
    debug: true,
    storage_backend: "local",
    auth_required: false,
  },
  export: { app_env: "local" },
  findings: [
    {
      check: "database_url",
      status: "PASS",
      message: "DATABASE_URL is configured.",
    },
  ],
};

const validation = {
  status: "PASSED",
  checks: [
    {
      check: "database",
      status: "PASS",
      message: "Database connectivity confirmed.",
    },
  ],
  fail_count: 0,
  warn_count: 0,
  pass_count: 1,
  policy_version: "1.0",
  engine_version: "8g.1.0",
};

const releaseCheck = {
  status: "PASSED",
  release,
  validation,
  disaster_recovery: { status: "READY" },
  restore: { status: "READY" },
  backup_records: [{ id: "1", kind: "database" }],
};

function stubHappyPath() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/system/version")) return response(version);
      if (url.includes("/system/release-check") && method === "POST") {
        return response(releaseCheck);
      }
      if (url.includes("/system/validate") && method === "POST") {
        return response(validation);
      }
      if (url.includes("/system/release")) return response(release);
      if (url.includes("/system/liveness")) return response(liveness);
      if (url.includes("/system/readiness")) return response(readiness);
      if (url.includes("/system/startup-validation")) return response(startup);
      if (url.includes("/system/configuration")) return response(configuration);
      return response(null, 404);
    }),
  );
}

describe("Phase 8G deployment UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubHappyPath();
  });

  it("renders SystemStatusPage panels", async () => {
    render(
      <TestProviders>
        <SystemStatusPage />
      </TestProviders>,
    );
    expect(screen.getByText("Deployment Status")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Liveness: alive/i)).toBeInTheDocument();
    });
    expect(screen.getByText("Health Overview")).toBeInTheDocument();
    expect(screen.getByText("Release")).toBeInTheDocument();
    expect(screen.getByText("Configuration")).toBeInTheDocument();
  });

  it("shows release metadata", async () => {
    render(
      <TestProviders>
        <ReleasePanel />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getAllByText(/20260906_0025/).length).toBeGreaterThan(0);
    });
    expect(screen.getByText("abc123")).toBeInTheDocument();
  });

  it("shows configuration findings", async () => {
    render(
      <TestProviders>
        <ConfigurationPanel />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("database_url")).toBeInTheDocument();
    });
  });

  it("runs validation from DeploymentPanel", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <DeploymentPanel />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/v0\.1\.0/)).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /Run validation/i }));
    await waitFor(() => {
      expect(screen.getByText(/1 pass · 0 warn · 0 fail/i)).toBeInTheDocument();
    });
  });

  it("handles health overview errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => response(null, 500)),
    );
    render(
      <TestProviders>
        <HealthOverview />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Health overview unavailable/i)).toBeInTheDocument();
    });
  });

  it("shows empty readiness checks", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/system/liveness")) return response(liveness);
        if (url.includes("/system/readiness")) {
          return response({ ...readiness, checks: [] });
        }
        if (url.includes("/system/startup-validation")) return response(startup);
        return response(null, 404);
      }),
    );
    render(
      <TestProviders>
        <HealthOverview />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/No checks/i)).toBeInTheDocument();
    });
  });
});
