import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TimelinePanel } from "../components/investigation/TimelinePanel";
import { TestProviders } from "./render";

const caseId = "00000000-0000-0000-0000-000000000801";

const timelineDetail = {
  id: "00000000-0000-0000-0000-000000000802",
  case_id: caseId,
  status: "SUCCEEDED" as const,
  engine_version: "1.0",
  policy_version: "1.0",
  event_count: 2,
  conflicts_count: 1,
  created_at: "2026-08-31T00:00:00Z",
  started_at: "2026-08-31T00:00:00Z",
  completed_at: "2026-08-31T00:00:01Z",
  error_code: null,
  error_message: null,
  metadata: {},
  provenance: { case_id: caseId },
  events: [
    {
      id: "00000000-0000-0000-0000-000000000803",
      timeline_id: "00000000-0000-0000-0000-000000000802",
      case_id: caseId,
      evidence_id: "00000000-0000-0000-0000-000000000804",
      event_id: "evidence_uploaded:804",
      event_type: "evidence_uploaded" as const,
      timestamp: "2026-08-31T00:00:00Z",
      timezone: "UTC",
      normalized_timestamp: "2026-08-31T00:00:00Z",
      confidence: 0.95,
      uncertainty_ms: 1000,
      description: "Evidence EVID-001 uploaded.",
      source: "evidence",
      source_id: "804",
      provenance: { evidence_id: "804", sha256_hash: "a".repeat(64) },
      metadata: {},
      supporting_artifacts: [],
      created_at: "2026-08-31T00:00:00Z",
    },
  ],
  conflicts: [
    {
      id: "00000000-0000-0000-0000-000000000805",
      timeline_id: "00000000-0000-0000-0000-000000000802",
      case_id: caseId,
      conflict_id: "multi_ts:804",
      conflict_type: "multiple_timestamps" as const,
      evidence_id: "00000000-0000-0000-0000-000000000804",
      involved_event_ids: ["metadata_exif:804", "metadata_filesystem:804"],
      explanation: "Multiple metadata timestamps exist for one artifact.",
      metadata: {},
      created_at: "2026-08-31T00:00:01Z",
    },
  ],
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
              message:
                status === 404
                  ? "No investigation timeline exists for this case."
                  : "The backend returned an unexpected error.",
              code: status === 404 ? "NOT_FOUND" : "API_ERROR",
              request_id: null,
            },
          },
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({})));
});

describe("Phase 7A TimelinePanel", () => {
  it("renders timeline events with confidence and source badges", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/timeline/latest")) {
          return response(timelineDetail);
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <TimelinePanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("Evidence EVID-001 uploaded.")).toBeInTheDocument();
    expect(screen.getByText(/confidence 95%/i)).toBeInTheDocument();
    expect(screen.getByText("evidence")).toBeInTheDocument();
  });

  it("shows loading state while timeline is generating", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/timeline/latest")) {
          return response({ ...timelineDetail, status: "RUNNING", events: [] });
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <TimelinePanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText(/Loading timeline/i)).toBeInTheDocument();
  });

  it("shows empty state when no timeline exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: false,
          status: 404,
          json: async () => ({
            success: false,
            error: {
              code: "NOT_FOUND",
              message: "No investigation timeline exists for this case.",
            },
          }),
        }),
      ),
    );
    render(
      <TestProviders>
        <TimelinePanel caseId={caseId} />
      </TestProviders>,
    );
    expect(
      await screen.findByText("No timeline events", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
  });

  it("shows error state for non-404 failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: async () => ({
            success: false,
            error: {
              code: "API_ERROR",
              message: "The backend returned an unexpected error.",
            },
          }),
        }),
      ),
    );
    render(
      <TestProviders>
        <TimelinePanel caseId={caseId} />
      </TestProviders>,
    );
    expect(
      await screen.findByText("Timeline unavailable", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
  });

  it("displays timestamp conflicts", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/timeline/latest")) {
          return response(timelineDetail);
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <TimelinePanel caseId={caseId} />
      </TestProviders>,
    );
    expect(
      await screen.findByText(/Multiple metadata timestamps exist/i),
    ).toBeInTheDocument();
  });

  it("expands provenance details", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/timeline/latest")) {
          return response(timelineDetail);
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <TimelinePanel caseId={caseId} />
      </TestProviders>,
    );
    await user.click(await screen.findByRole("button", { name: /Provenance/i }));
    expect(await screen.findByText(/sha256_hash/i)).toBeInTheDocument();
  });
});
