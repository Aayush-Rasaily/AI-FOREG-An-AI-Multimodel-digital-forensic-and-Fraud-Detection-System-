import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuditTrailPanel } from "../components/investigation/AuditTrailPanel";
import { TestProviders } from "./render";

const caseId = "00000000-0000-0000-0000-000000000e01";

const auditEvent = {
  id: "00000000-0000-0000-0000-000000000e02",
  timestamp: "2026-09-01T00:00:00Z",
  user: "system",
  operation: "case.created",
  category: "case",
  case_id: caseId,
  evidence_id: null,
  previous_state: null,
  new_state: { title: "Test Case" },
  client_ip: "127.0.0.1",
  user_agent: "test-agent",
  engine_version: "1.0",
  policy_version: "1.0",
  sha256_checksum: null,
  integrity_hash: "a".repeat(64),
  metadata: {},
};

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () =>
      status >= 200 && status < 300
        ? { success: true, data }
        : {
            success: false,
            error: {
              message: status === 404 ? "Not found." : "Error.",
              code: status === 404 ? "NOT_FOUND" : "API_ERROR",
              request_id: null,
            },
          },
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({})));
});

describe("Phase 7E AuditTrailPanel", () => {
  it("renders audit events", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/audit")) {
          return response({
            items: [auditEvent],
            total: 1,
            limit: 50,
            offset: 0,
          });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <AuditTrailPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByRole("heading", { name: "Audit Trail" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("case.created", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
    expect(screen.getByText("1 events")).toBeInTheDocument();
  });

  it("shows empty state when no events", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/audit")) {
          return response({
            items: [],
            total: 0,
            limit: 50,
            offset: 0,
          });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <AuditTrailPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByText("No audit events", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
  });

  it("shows error state on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/audit")) {
          return response(null, 500);
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <AuditTrailPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByText(
        "Audit trail unavailable",
        {},
        { timeout: 5000 },
      ),
    ).toBeInTheDocument();
  });

  it("expands an audit event", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/audit")) {
          return response({
            items: [auditEvent],
            total: 1,
            limit: 50,
            offset: 0,
          });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <AuditTrailPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByText("case.created", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
    await user.click(screen.getByText("case.created"));
    expect(screen.getByText(/User: system/)).toBeInTheDocument();
    expect(screen.getByText(/Integrity:/)).toBeInTheDocument();
  });

  it("exposes verify and export buttons", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/audit")) {
          return response({
            items: [auditEvent],
            total: 1,
            limit: 50,
            offset: 0,
          });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <AuditTrailPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByRole("button", { name: /Verify Integrity/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Export/i }),
    ).toBeInTheDocument();
  });

  it("filters events by search term", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/audit")) {
          return response({
            items: [
              auditEvent,
              { ...auditEvent, id: "00000000-0000-0000-0000-000000000e03", operation: "evidence.uploaded", category: "evidence" },
            ],
            total: 2,
            limit: 50,
            offset: 0,
          });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <AuditTrailPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByText("case.created", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
    expect(screen.getByText("evidence.uploaded")).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("Filter events…"), "evidence");
    expect(screen.queryByText("case.created")).not.toBeInTheDocument();
    expect(screen.getByText("evidence.uploaded")).toBeInTheDocument();
  });
});
