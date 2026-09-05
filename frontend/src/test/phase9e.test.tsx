import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApprovalPanel } from "../components/case-review/ApprovalPanel";
import { CaseReviewPanel } from "../components/case-review/CaseReviewPanel";
import { ReviewHistoryPanel } from "../components/case-review/ReviewHistoryPanel";
import { ReviewMetricsPanel } from "../components/case-review/ReviewMetricsPanel";
import { ValidationChecklist } from "../components/case-review/ValidationChecklist";
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
  id: "rev-1",
  case_id: "case-1",
  status: "SUCCEEDED",
  stage: "UNDER_REVIEW",
  checklist_count: 1,
  approval_count: 0,
  metrics: {
    validation_pct: 0.4,
    evidence_coverage_pct: 1,
    review_completion_pct: 0.5,
    approval_completion_pct: 0,
    outstanding_issues: 2,
    blocking_issues: 1,
  },
  outstanding: ["Timeline Reviewed"],
  blocking: ["Final Validation"],
  required_roles: ["TECHNICAL_REVIEWER", "FORENSIC_REVIEWER"],
  provenance: {
    engine_version: "9e.1.0",
    sources: ["case", "evidence"],
  },
  engine_version: "9e.1.0",
  policy_version: "1.0",
  created_at: "2026-09-11T00:00:00Z",
  completed_at: "2026-09-11T00:00:01Z",
  checklist: [
    {
      id: "item-1",
      item_key: "critem_1",
      item_code: "SHA256_VERIFIED",
      title: "SHA256 Verified",
      status: "PENDING",
      suggested_status: "PASS",
      blocking: false,
      outstanding: true,
      notes: "Hashes present.",
      provenance: { engine_version: "9e.1.0" },
    },
  ],
  approvals: [],
  persisted: true,
};

const history = [
  {
    id: "rev-1",
    case_id: "case-1",
    status: "SUCCEEDED",
    stage: "UNDER_REVIEW",
    checklist_count: 1,
    approval_count: 0,
    metrics: run.metrics,
    engine_version: "9e.1.0",
    policy_version: "1.0",
    created_at: "2026-09-11T00:00:00Z",
  },
];

function stubApi(overrides?: { latestStatus?: number }) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/case-review/approvals") && method === "POST") {
        return response({
          id: "appr-1",
          case_id: "case-1",
          reviewer: "investigator",
          approver_role: "TECHNICAL_REVIEWER",
          decision: "APPROVED",
          comments: "ok",
          provenance: {},
          created_at: "2026-09-11T00:00:02Z",
        });
      }
      if (url.includes("/case-review") && method === "POST") {
        return response(run);
      }
      if (url.includes("/case-review/checklist/") && method === "PATCH") {
        return response({ ...run.checklist[0], status: "PASS" });
      }
      if (url.includes("/case-review/history")) {
        return response({ items: history, total: 1 });
      }
      if (url.includes("/case-review")) {
        if ((overrides?.latestStatus ?? 200) >= 400) {
          return response(null, overrides?.latestStatus);
        }
        return response(run);
      }
      return response(null, 404);
    }),
  );
}

describe("Phase 9E case review UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubApi();
  });

  it("renders review dashboard", async () => {
    render(
      <TestProviders>
        <CaseReviewPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getAllByText("SUCCEEDED").length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText("UNDER_REVIEW").length).toBeGreaterThan(0);
  });

  it("shows empty state", async () => {
    stubApi({ latestStatus: 404 });
    render(
      <TestProviders>
        <CaseReviewPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("No case review")).toBeInTheDocument();
    });
  });

  it("shows error state", async () => {
    stubApi({ latestStatus: 500 });
    render(
      <TestProviders>
        <CaseReviewPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("Case review unavailable")).toBeInTheDocument();
    });
  });

  it("shows loading then metrics", async () => {
    render(
      <TestProviders>
        <CaseReviewPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("40% validated")).toBeInTheDocument();
    });
  });

  it("starts review on button click", async () => {
    stubApi({ latestStatus: 404 });
    const user = userEvent.setup();
    render(
      <TestProviders>
        <CaseReviewPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Start review/i }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /Start review/i }));
  });

  it("renders checklist", () => {
    render(
      <TestProviders>
        <ValidationChecklist
          items={run.checklist}
          search=""
          statusFilter="all"
        />
      </TestProviders>,
    );
    expect(screen.getByText("SHA256 Verified")).toBeInTheDocument();
  });

  it("filters checklist by search", () => {
    render(
      <TestProviders>
        <ValidationChecklist
          items={run.checklist}
          search="missing"
          statusFilter="all"
        />
      </TestProviders>,
    );
    expect(screen.getByText("No checklist items match.")).toBeInTheDocument();
  });

  it("renders approval panel", () => {
    render(
      <TestProviders>
        <ApprovalPanel
          approvals={[]}
          requiredRoles={run.required_roles}
        />
      </TestProviders>,
    );
    expect(screen.getByText("Approval Chain")).toBeInTheDocument();
    expect(screen.getByText("TECHNICAL_REVIEWER")).toBeInTheDocument();
  });

  it("renders metrics with blocking issues", () => {
    render(
      <TestProviders>
        <ReviewMetricsPanel
          blocking={run.blocking}
          metrics={run.metrics}
          outstanding={run.outstanding}
          stage={run.stage}
        />
      </TestProviders>,
    );
    expect(screen.getByText("Final Validation")).toBeInTheDocument();
    expect(screen.getByText("Timeline Reviewed")).toBeInTheDocument();
  });

  it("renders review history", () => {
    render(
      <TestProviders>
        <ReviewHistoryPanel items={history} />
      </TestProviders>,
    );
    expect(screen.getByText(/engine 9e.1.0/)).toBeInTheDocument();
  });

  it("shows provenance on dashboard", async () => {
    render(
      <TestProviders>
        <CaseReviewPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Provenance · engine 9e.1.0/)).toBeInTheDocument();
    });
  });
});
