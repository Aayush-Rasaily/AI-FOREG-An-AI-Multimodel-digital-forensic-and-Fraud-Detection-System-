import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReportPanel } from "../components/investigation/ReportPanel";
import { TestProviders } from "./render";

const caseId = "00000000-0000-0000-0000-000000000d01";

const reportDetail = {
  id: "00000000-0000-0000-0000-000000000d02",
  case_id: caseId,
  status: "COMPLETED" as const,
  report_version: "2.0",
  engine_version: "2.0",
  fusion_policy_version: null,
  case_intelligence_policy_version: null,
  case_intelligence_run_id: null,
  evidence_count: 1,
  evidence_hashes: ["a".repeat(64)],
  pdf_sha256: null,
  has_pdf: false,
  report_checksum: "b".repeat(64),
  included_analysis_run_ids: {},
  created_at: "2026-09-01T00:00:00Z",
  started_at: "2026-09-01T00:00:00Z",
  completed_at: "2026-09-01T00:00:01Z",
  error_code: null,
  error_message: null,
  metadata: {},
  provenance: { case_id: caseId },
  executive_summary: { evidence_count: 1 },
  explainability: {},
  section_order: ["case_summary", "evidence_inventory", "correlation_summary"],
  content: {
    report_id: "00000000-0000-0000-0000-000000000d02",
    report_checksum: "b".repeat(64),
    section_order: ["case_summary", "evidence_inventory", "correlation_summary"],
    sections: {
      case_summary: { available: true, executive_summary: { evidence_count: 1 } },
      evidence_inventory: {
        available: true,
        count: 1,
        items: [{ evidence_number: "EV-1", summary: "EV-1 file.pdf" }],
      },
      correlation_summary: {
        available: false,
        count: 0,
        items: [],
        note: "Cross-evidence correlation analysis not available.",
      },
    },
  },
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
                  ? "No forensic report exists for this case."
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

describe("Phase 7D ReportPanel", () => {
  it("renders report sections and checksum", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/reports/latest")) {
          return response(reportDetail);
        }
        if (url.includes("/reports?")) {
          return response({ items: [reportDetail], total: 1, limit: 50, offset: 0 });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <ReportPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByRole("heading", { name: "Investigation Report" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("Case Summary", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
    expect(document.body.textContent).toContain(`Checksum: ${"b".repeat(64)}`);
    expect(screen.getByText("Evidence Inventory")).toBeInTheDocument();
  });

  it("shows loading while generating", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/reports/latest")) {
          return response({ ...reportDetail, status: "GENERATING", content: {} });
        }
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }),
    );

    render(
      <TestProviders>
        <ReportPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByText(/Loading investigation report/i),
    ).toBeInTheDocument();
  });

  it("shows empty state on 404", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/reports/latest")) {
          return response(null, 404);
        }
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }),
    );

    render(
      <TestProviders>
        <ReportPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(await screen.findByText("No reports", {}, { timeout: 5000 })).toBeInTheDocument();
  });

  it("shows error state on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/reports/latest")) {
          return response(null, 500);
        }
        return response({ items: [], total: 0, limit: 50, offset: 0 });
      }),
    );

    render(
      <TestProviders>
        <ReportPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByText("Report unavailable", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
  });

  it("expands a report section", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/reports/latest")) {
          return response(reportDetail);
        }
        return response({ items: [reportDetail], total: 1, limit: 50, offset: 0 });
      }),
    );

    render(
      <TestProviders>
        <ReportPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(await screen.findByText("Evidence Inventory")).toBeInTheDocument();
    await user.click(screen.getByText("Evidence Inventory"));
    expect(screen.getByText(/EV-1/)).toBeInTheDocument();
  });

  it("exposes download buttons for json md html", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/reports/latest")) {
          return response(reportDetail);
        }
        return response({ items: [reportDetail], total: 1, limit: 50, offset: 0 });
      }),
    );

    render(
      <TestProviders>
        <ReportPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(await screen.findByRole("button", { name: /JSON/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Markdown/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /HTML/i })).toBeInTheDocument();
  });
});
