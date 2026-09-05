import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DecisionLogPanel } from "../components/decision-support/DecisionLogPanel";
import { ReviewQueuePanel } from "../components/decision-support/ReviewQueuePanel";
import { WorkflowDashboard } from "../components/decision-support/WorkflowDashboard";
import { WorkflowMetricsPanel } from "../components/decision-support/WorkflowMetricsPanel";
import { WorkflowTaskPanel } from "../components/decision-support/WorkflowTaskPanel";
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
  current_stage: "COLLECT",
  task_count: 1,
  review_count: 1,
  metrics: {
    open_tasks: 1,
    completed_tasks: 0,
    pending_reviews: 1,
    average_priority: 0.8,
    critical_evidence_count: 1,
    workflow_completion: 0,
    investigation_progress: 0.35,
    evidence_review_coverage: 1,
  },
  open_conflicts: [],
  provenance: { engine_version: "9d.1.0" },
  engine_version: "9d.1.0",
  policy_version: "1.0",
  created_at: "2026-09-10T00:00:00Z",
  completed_at: "2026-09-10T00:00:01Z",
  tasks: [
    {
      id: "task-1",
      task_key: "dstask_1",
      task_type: "ACQUIRE_ORIGINAL_EVIDENCE",
      stage: "COLLECT",
      title: "Acquire Original Evidence",
      description: "Acquire initial case evidence.",
      priority: "HIGH",
      status: "OPEN",
      estimated_effort_hours: 4,
      priority_score: 0.92,
      required_evidence_ids: [],
      supporting_intelligence: {},
      provenance: { engine_version: "9d.1.0" },
    },
  ],
  review_queue: [
    {
      queue_key: "dsrev_1",
      evidence_id: "ev-1",
      priority: "HIGH",
      priority_score: 0.9,
      reasons: ["incomplete_custody"],
      provenance: {},
    },
  ],
  persisted: true,
};

function stubApi(overrides?: { latestStatus?: number }) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/decision-support") && method === "POST") {
        if (url.includes("/decisions")) {
          return response({
            id: "dec-1",
            case_id: "case-1",
            decision_type: "MARKED_REVIEWED",
            investigator: "investigator",
            justification: "ok",
            provenance: {},
            created_at: "2026-09-10T00:00:02Z",
          });
        }
        return response(run);
      }
      if (url.includes("/decision-support/decisions")) {
        return response({ items: [], total: 0 });
      }
      if (url.includes("/decision-support") && method === "PATCH") {
        return response({ ...run.tasks[0], status: "COMPLETED" });
      }
      if (url.includes("/decision-support")) {
        if ((overrides?.latestStatus ?? 200) >= 400) {
          return response(null, overrides?.latestStatus);
        }
        return response(run);
      }
      return response(null, 404);
    }),
  );
}

describe("Phase 9D decision support UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubApi();
  });

  it("renders workflow dashboard", async () => {
    render(
      <TestProviders>
        <WorkflowDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getAllByText("SUCCEEDED").length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText("COLLECT").length).toBeGreaterThan(0);
  });

  it("shows empty state", async () => {
    stubApi({ latestStatus: 404 });
    render(
      <TestProviders>
        <WorkflowDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("No decision-support plan")).toBeInTheDocument();
    });
  });

  it("shows error state", async () => {
    stubApi({ latestStatus: 500 });
    render(
      <TestProviders>
        <WorkflowDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("Workflow unavailable")).toBeInTheDocument();
    });
  });

  it("shows loading then content", async () => {
    render(
      <TestProviders>
        <WorkflowDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("35% progress")).toBeInTheDocument();
    });
  });

  it("plans workflow on button click", async () => {
    stubApi({ latestStatus: 404 });
    const user = userEvent.setup();
    render(
      <TestProviders>
        <WorkflowDashboard caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Plan workflow/i }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /Plan workflow/i }));
  });

  it("renders task board", () => {
    render(
      <TestProviders>
        <WorkflowTaskPanel
          search=""
          stageFilter="all"
          tasks={run.tasks}
        />
      </TestProviders>,
    );
    expect(screen.getByText("Acquire Original Evidence")).toBeInTheDocument();
  });

  it("renders review queue", () => {
    render(
      <TestProviders>
        <ReviewQueuePanel items={run.review_queue} search="" />
      </TestProviders>,
    );
    expect(screen.getByText("ev-1")).toBeInTheDocument();
    expect(screen.getByText(/incomplete_custody/i)).toBeInTheDocument();
  });

  it("renders metrics", () => {
    render(
      <TestProviders>
        <WorkflowMetricsPanel
          currentStage="COLLECT"
          metrics={run.metrics}
        />
      </TestProviders>,
    );
    expect(screen.getByText("Investigation progress")).toBeInTheDocument();
    expect(screen.getByText("35%")).toBeInTheDocument();
  });

  it("renders decision log empty", () => {
    render(
      <TestProviders>
        <DecisionLogPanel decisions={[]} />
      </TestProviders>,
    );
    expect(screen.getByText("No decisions")).toBeInTheDocument();
  });

  it("filters tasks by search", () => {
    render(
      <TestProviders>
        <WorkflowTaskPanel
          search="zzzz"
          stageFilter="all"
          tasks={run.tasks}
        />
      </TestProviders>,
    );
    expect(screen.getByText("No tasks")).toBeInTheDocument();
  });
});
