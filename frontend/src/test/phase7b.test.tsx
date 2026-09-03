import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EvidenceCorrelationPanel } from "../components/investigation/EvidenceCorrelationPanel";
import { TestProviders } from "./render";

const caseId = "00000000-0000-0000-0000-000000000901";

const correlationDetail = {
  id: "00000000-0000-0000-0000-000000000902",
  case_id: caseId,
  status: "SUCCEEDED" as const,
  engine_version: "1.0",
  policy_version: "1.0",
  correlation_count: 2,
  evidence_count: 2,
  created_at: "2026-08-31T00:00:00Z",
  started_at: "2026-08-31T00:00:00Z",
  completed_at: "2026-08-31T00:00:01Z",
  error_code: null,
  error_message: null,
  metadata: {},
  provenance: { case_id: caseId },
  correlations: [
    {
      id: "00000000-0000-0000-0000-000000000903",
      analysis_run_id: "00000000-0000-0000-0000-000000000902",
      case_id: caseId,
      left_evidence_id: "00000000-0000-0000-0000-000000000904",
      right_evidence_id: "00000000-0000-0000-0000-000000000905",
      correlation_id: "same_email:904:905",
      correlation_type: "same_email" as const,
      score: 0.98,
      confidence: 0.95,
      explanation: "Evidence share the same email: shared@example.com.",
      supporting_findings: [],
      supporting_metadata: { email: "shared@example.com" },
      supporting_entities: ["shared@example.com"],
      provenance: { case_id: caseId },
      supports: [
        {
          id: "00000000-0000-0000-0000-000000000906",
          support_kind: "shared_value",
          support_ref: "email:shared@example.com",
          label: "email",
          value: "shared@example.com",
          metadata: {},
        },
      ],
      created_at: "2026-08-31T00:00:01Z",
    },
    {
      id: "00000000-0000-0000-0000-000000000907",
      analysis_run_id: "00000000-0000-0000-0000-000000000902",
      case_id: caseId,
      left_evidence_id: "00000000-0000-0000-0000-000000000904",
      right_evidence_id: "00000000-0000-0000-0000-000000000905",
      correlation_id: "similar_filename:904:905",
      correlation_type: "similar_filename" as const,
      score: 0.45,
      confidence: 0.6,
      explanation: "Original filenames share overlapping tokens.",
      supporting_findings: [],
      supporting_metadata: {},
      supporting_entities: ["invoice_a.pdf", "invoice_b.pdf"],
      provenance: { case_id: caseId },
      supports: [],
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
                  ? "No correlation analysis exists for this case."
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

describe("Phase 7B EvidenceCorrelationPanel", () => {
  it("renders correlations with score and confidence", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/correlations/latest")) {
          return response(correlationDetail);
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <EvidenceCorrelationPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(
      await screen.findByText(/Evidence share the same email/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/score 98%/i)).toBeInTheDocument();
    expect(screen.getByText(/confidence 95%/i)).toBeInTheDocument();
  });

  it("shows loading while analyzing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/correlations/latest")) {
          return response({
            ...correlationDetail,
            status: "RUNNING",
            correlations: [],
          });
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <EvidenceCorrelationPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText(/Loading correlations/i)).toBeInTheDocument();
  });

  it("shows empty state when no analysis exists", async () => {
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
              message: "No correlation analysis exists for this case.",
            },
          }),
        }),
      ),
    );
    render(
      <TestProviders>
        <EvidenceCorrelationPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(
      await screen.findByText("No correlations", {}, { timeout: 5000 }),
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
        <EvidenceCorrelationPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(
      await screen.findByText("Correlations unavailable", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
  });

  it("expands provenance details", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/correlations/latest")) {
          return response(correlationDetail);
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <EvidenceCorrelationPanel caseId={caseId} />
      </TestProviders>,
    );
    const buttons = await screen.findAllByRole("button", { name: /Provenance/i });
    await user.click(buttons[0]);
    expect(await screen.findByText(/support_kind/i)).toBeInTheDocument();
    expect(screen.getByText(/shared_value/i)).toBeInTheDocument();
  });

  it("filters by correlation type", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/correlations/latest")) {
          return response(correlationDetail);
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <EvidenceCorrelationPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(
      await screen.findByText(/Evidence share the same email/i),
    ).toBeInTheDocument();
    await user.selectOptions(
      screen.getByLabelText(/Filter correlation type/i),
      "similar_filename",
    );
    expect(
      screen.queryByText(/Evidence share the same email/i),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/overlapping tokens/i)).toBeInTheDocument();
  });
});
