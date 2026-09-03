import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ActivityPanel } from "../components/collaboration/ActivityPanel";
import { CaseMembersPanel } from "../components/collaboration/CaseMembersPanel";
import { CommentsPanel } from "../components/collaboration/CommentsPanel";
import { TaskBoard } from "../components/collaboration/TaskBoard";
import { WorkflowPanel } from "../components/collaboration/WorkflowPanel";
import { TestProviders } from "./render";

const caseId = "00000000-0000-0000-0000-000000000c01";

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
              message: "Error.",
              code: "API_ERROR",
              request_id: null,
            },
          },
  });
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: RequestInfo) => {
      const url = String(input);
      if (url.includes("/members")) {
        return response({
          items: [
            {
              id: "m1",
              case_id: caseId,
              user_id: "u1",
              username: "admin",
              display_name: "Administrator",
              role: "owner",
              invited_by: null,
              created_at: "2026-09-02T00:00:00Z",
            },
          ],
          total: 1,
        });
      }
      if (url.includes("/tasks")) {
        return response({
          items: [
            {
              id: "t1",
              case_id: caseId,
              title: "Review packet",
              description: null,
              assignee_id: null,
              created_by: "u1",
              priority: "high",
              status: "open",
              due_date: null,
              linked_evidence_id: null,
              linked_report_id: null,
              completed_at: null,
              created_at: "2026-09-02T00:00:00Z",
              updated_at: "2026-09-02T00:00:00Z",
            },
          ],
          total: 1,
        });
      }
      if (url.includes("/comments/")) {
        return response({
          items: [
            {
              id: "c1",
              case_id: caseId,
              author_id: "u1",
              author_username: "admin",
              resource_type: "case",
              resource_id: caseId,
              parent_id: null,
              body: "Hello team",
              body_markdown: true,
              edit_history: [],
              is_deleted: false,
              mentions: [],
              created_at: "2026-09-02T00:00:00Z",
              updated_at: "2026-09-02T00:00:00Z",
            },
          ],
          total: 1,
        });
      }
      if (url.includes("/activity")) {
        return response({
          items: [
            {
              id: "a1",
              case_id: caseId,
              actor_id: "u1",
              actor_username: "admin",
              action: "task.created",
              summary: "Task created: Review packet",
              details: {},
              created_at: "2026-09-02T00:00:00Z",
            },
          ],
          total: 1,
        });
      }
      if (url.includes("/workflow")) {
        return response({
          case_id: caseId,
          stage: "open",
          version: 1,
          updated_by: null,
          updated_at: "2026-09-02T00:00:00Z",
          allowed_transitions: ["evidence_collection"],
        });
      }
      return response({});
    }),
  );
});

describe("Phase 8B collaboration frontend", () => {
  it("renders case members", async () => {
    render(
      <TestProviders>
        <CaseMembersPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("Team members")).toBeInTheDocument();
    expect(await screen.findByText("Administrator")).toBeInTheDocument();
  });

  it("renders tasks", async () => {
    render(
      <TestProviders>
        <TaskBoard caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("Tasks")).toBeInTheDocument();
    expect(await screen.findByText("Review packet")).toBeInTheDocument();
  });

  it("renders comments", async () => {
    render(
      <TestProviders>
        <CommentsPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("Comments")).toBeInTheDocument();
    expect(await screen.findByText("Hello team")).toBeInTheDocument();
  });

  it("renders activity feed", async () => {
    render(
      <TestProviders>
        <ActivityPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("Activity")).toBeInTheDocument();
    expect(
      await screen.findByText("Task created: Review packet"),
    ).toBeInTheDocument();
  });

  it("renders workflow controls", async () => {
    render(
      <TestProviders>
        <WorkflowPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("Workflow")).toBeInTheDocument();
    expect(
      await screen.findByRole("button", {
        name: /Advance to evidence collection/i,
      }),
    ).toBeInTheDocument();
  });
});
