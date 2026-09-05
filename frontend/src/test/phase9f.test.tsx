import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AlertPanel } from "../components/integrity/AlertPanel";
import { DriftViewer } from "../components/integrity/DriftViewer";
import { IntegrityDashboard } from "../components/integrity/IntegrityDashboard";
import { IntegrityTimeline } from "../components/integrity/IntegrityTimeline";
import { VerificationHistory } from "../components/integrity/VerificationHistory";
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
  id: "im-1",
  case_id: "case-1",
  status: "SUCCEEDED",
  check_count: 2,
  alert_count: 1,
  drift_count: 1,
  metrics: {
    checks_total: 2,
    checks_passed: 1,
    checks_failed: 1,
    checks_warned: 0,
    alert_count: 1,
    drift_count: 1,
    evidence_coverage_pct: 1,
    integrity_score: 0.72,
    critical_alerts: 1,
    high_alerts: 0,
  },
  timeline: [
    {
      evidence_id: "e1",
      event: "integrity_evaluated",
      custody_events: 1,
      storage_present: true,
    },
  ],
  fingerprints: {},
  provenance: { engine_version: "9f.1.0" },
  engine_version: "9f.1.0",
  policy_version: "1.0",
  created_at: "2026-09-12T00:00:00Z",
  completed_at: "2026-09-12T00:00:01Z",
  checks: [],
  alerts: [
    {
      alert_key: "a1",
      alert_code: "SHA256_CONSISTENCY",
      severity: "CRITICAL",
      title: "SHA-256 Consistency",
      message: "Custody hash mismatch.",
      evidence_id: "e1",
      provenance: {},
    },
  ],
  drifts: [
    {
      drift_key: "d1",
      evidence_id: "e1",
      field_name: "metadata",
      previous_value: "aaa",
      current_value: "bbb",
      message: "Metadata changed.",
      provenance: {},
    },
  ],
  persisted: true,
};

const history = [
  {
    id: "im-1",
    case_id: "case-1",
    status: "SUCCEEDED",
    check_count: 2,
    alert_count: 1,
    drift_count: 1,
    metrics: run.metrics,
    engine_version: "9f.1.0",
    policy_version: "1.0",
    created_at: "2026-09-12T00:00:00Z",
  },
];

function stubApi(overrides?: { latestStatus?: number }) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/integrity-check") && method === "POST") {
        return response(run);
      }
      if (url.includes("/integrity/history")) {
        return response({ items: history, total: 1 });
      }
      if (url.includes("/integrity")) {
        if ((overrides?.latestStatus ?? 200) >= 400) {
          return response(null, overrides?.latestStatus);
        }
        return response(run);
      }
      return response(null, 404);
    }),
  );
}

describe("Phase 9F integrity UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubApi();
  });

  it("renders integrity dashboard", async () => {
    render(
      <TestProviders>
        <IntegrityDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getAllByText("SUCCEEDED").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("72% score")).toBeInTheDocument();
  });

  it("shows empty state", async () => {
    stubApi({ latestStatus: 404 });
    render(
      <TestProviders>
        <IntegrityDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("No integrity run")).toBeInTheDocument();
    });
  });

  it("shows error state", async () => {
    stubApi({ latestStatus: 500 });
    render(
      <TestProviders>
        <IntegrityDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("Integrity unavailable")).toBeInTheDocument();
    });
  });

  it("runs integrity check on button click", async () => {
    stubApi({ latestStatus: 404 });
    const user = userEvent.setup();
    render(
      <TestProviders>
        <IntegrityDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Run integrity check/i }),
      ).toBeInTheDocument();
    });
    await user.click(
      screen.getByRole("button", { name: /Run integrity check/i }),
    );
  });

  it("renders alert panel", () => {
    render(
      <TestProviders>
        <AlertPanel alerts={run.alerts} search="" />
      </TestProviders>,
    );
    expect(screen.getByText("SHA-256 Consistency")).toBeInTheDocument();
  });

  it("filters alerts by search", () => {
    render(
      <TestProviders>
        <AlertPanel alerts={run.alerts} search="missing" />
      </TestProviders>,
    );
    expect(screen.getByText("No alerts.")).toBeInTheDocument();
  });

  it("renders drift viewer", () => {
    render(
      <TestProviders>
        <DriftViewer drifts={run.drifts} />
      </TestProviders>,
    );
    expect(screen.getByText(/metadata · evidence e1/i)).toBeInTheDocument();
  });

  it("renders timeline", () => {
    render(
      <TestProviders>
        <IntegrityTimeline timeline={run.timeline} />
      </TestProviders>,
    );
    expect(screen.getByText(/integrity_evaluated/)).toBeInTheDocument();
  });

  it("renders verification history", () => {
    render(
      <TestProviders>
        <VerificationHistory items={history} />
      </TestProviders>,
    );
    expect(screen.getByText(/engine 9f.1.0/)).toBeInTheDocument();
  });

  it("shows provenance on dashboard", async () => {
    render(
      <TestProviders>
        <IntegrityDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Provenance · engine 9f.1.0/)).toBeInTheDocument();
    });
  });
});
