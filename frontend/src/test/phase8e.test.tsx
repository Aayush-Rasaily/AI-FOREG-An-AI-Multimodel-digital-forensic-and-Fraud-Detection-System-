import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MilestoneTimeline } from "../components/workflow/MilestoneTimeline";
import { NotesPanel } from "../components/workflow/NotesPanel";
import { NotificationsPanel } from "../components/workflow/NotificationsPanel";
import { ReviewPanel } from "../components/workflow/ReviewPanel";
import { TaskBoard } from "../components/workflow/TaskBoard";
import { WorkflowPanel } from "../components/workflow/WorkflowPanel";
import { WorkflowStatusBadge } from "../components/workflow/WorkflowStatusBadge";
import { TestProviders } from "./render";

const caseId = "case-8e";

const workflow = {
  id: "wf-1",
  case_id: caseId,
  status: "ACTIVE",
  assigned_analyst_id: null,
  allowed_transitions: ["UNDER_REVIEW", "ARCHIVED"],
  activity: [
    {
      action: "status_changed",
      summary: "Status changed from NEW to ACTIVE",
      actor_id: null,
      actor_username: "system",
      timestamp: "2026-09-05T00:00:00Z",
      details: {},
    },
  ],
  policy_version: "1.0",
  engine_version: "8e.1.0",
  created_at: "2026-09-05T00:00:00Z",
  updated_at: "2026-09-05T00:00:00Z",
  status_changed_at: "2026-09-05T00:00:00Z",
  status_changed_by: null,
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
            error: { message: "failed", code: "ERR", request_id: "r1" },
          },
  });
}

describe("Phase 8E workflow UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/investigation-workflow") && !url.includes("/status")) {
          return response(workflow);
        }
        if (url.includes("/workflow-tasks")) {
          return response({
            items: [
              {
                id: "t1",
                workflow_id: "wf-1",
                case_id: caseId,
                task_type: "GENERAL",
                title: "Review packet",
                description: null,
                status: "OPEN",
                assignee_id: null,
                created_by: null,
                linked_evidence_id: null,
                linked_report_id: null,
                completed_at: null,
                cancelled_at: null,
                created_at: "2026-09-05T00:00:00Z",
                updated_at: "2026-09-05T00:00:00Z",
              },
            ],
            total: 1,
          });
        }
        if (url.includes("/workflow-reviews")) {
          return response({
            items: [
              {
                id: "r1",
                workflow_id: "wf-1",
                case_id: caseId,
                review_kind: "evidence",
                status: "PENDING",
                evidence_id: "e1",
                report_id: null,
                reviewer_id: null,
                comments: "Needs hash check",
                reason: null,
                decided_at: null,
                history: [],
                created_by: null,
                created_at: "2026-09-05T00:00:00Z",
                updated_at: "2026-09-05T00:00:00Z",
              },
            ],
            total: 1,
          });
        }
        if (url.includes("/workflow-notes")) {
          return response({
            items: [
              {
                id: "n1",
                workflow_id: "wf-1",
                case_id: caseId,
                category: "analytical",
                visibility: "internal",
                content_markdown: "First note",
                author_id: null,
                history: [{ version: 1 }],
                created_at: "2026-09-05T00:00:00Z",
                updated_at: "2026-09-05T00:00:00Z",
              },
            ],
            total: 1,
          });
        }
        if (url.includes("/workflow-milestones")) {
          return response({
            items: [
              {
                id: "m1",
                workflow_id: "wf-1",
                case_id: caseId,
                milestone_type: "Investigation Started",
                label: "Investigation Started",
                reached_at: "2026-09-05T00:00:00Z",
                reached_by: null,
                auto_derived: true,
                details: {},
                created_at: "2026-09-05T00:00:00Z",
              },
            ],
            total: 1,
          });
        }
        if (url.includes("/workflow-notifications")) {
          return response({
            items: [
              {
                id: "nt1",
                workflow_id: "wf-1",
                case_id: caseId,
                user_id: "u1",
                kind: "assigned_task",
                title: "Task assigned",
                body: "You were assigned: Review packet",
                status: "unread",
                payload: {},
                created_at: "2026-09-05T00:00:00Z",
              },
            ],
            total: 1,
          });
        }
        return response({}, 500);
      }),
    );
  });

  it("renders workflow status and activity", async () => {
    render(
      <TestProviders>
        <WorkflowPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("ACTIVE")).toBeInTheDocument();
    expect(
      await screen.findByText("Status changed from NEW to ACTIVE"),
    ).toBeInTheDocument();
    expect(screen.getByText(/Advance to UNDER REVIEW/i)).toBeInTheDocument();
  });

  it("renders task board, reviews, notes, milestones, notifications", async () => {
    render(
      <TestProviders>
        <TaskBoard caseId={caseId} />
        <ReviewPanel caseId={caseId} />
        <NotesPanel caseId={caseId} />
        <MilestoneTimeline caseId={caseId} />
        <NotificationsPanel caseId={caseId} />
        <WorkflowStatusBadge status="APPROVED" />
      </TestProviders>,
    );
    expect(await screen.findByText("Review packet")).toBeInTheDocument();
    expect(await screen.findByText("Needs hash check")).toBeInTheDocument();
    expect(await screen.findByText("First note")).toBeInTheDocument();
    expect(
      await screen.findByText("Investigation Started"),
    ).toBeInTheDocument();
    expect(await screen.findByText("Task assigned")).toBeInTheDocument();
    expect(screen.getByText("APPROVED")).toBeInTheDocument();
  });

  it("shows empty and error states", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/workflow-tasks")) {
          return response({ items: [], total: 0 });
        }
        if (url.includes("/workflow-notes")) {
          return response({}, 500);
        }
        return response({ items: [], total: 0 });
      }),
    );

    render(
      <TestProviders>
        <TaskBoard caseId={caseId} />
        <NotesPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("No workflow tasks")).toBeInTheDocument();
    expect(await screen.findByText("Error")).toBeInTheDocument();
  });
});
