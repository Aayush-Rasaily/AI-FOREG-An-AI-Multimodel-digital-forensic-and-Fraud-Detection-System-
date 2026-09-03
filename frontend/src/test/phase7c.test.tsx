import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EntityGraphPanel } from "../components/investigation/EntityGraphPanel";
import { TestProviders } from "./render";

const caseId = "00000000-0000-0000-0000-000000000a01";

const entityDetail = {
  id: "00000000-0000-0000-0000-000000000a02",
  case_id: caseId,
  status: "SUCCEEDED" as const,
  engine_version: "1.0",
  policy_version: "1.0",
  entity_count: 2,
  relationship_count: 1,
  evidence_count: 2,
  created_at: "2026-09-01T00:00:00Z",
  started_at: "2026-09-01T00:00:00Z",
  completed_at: "2026-09-01T00:00:01Z",
  error_code: null,
  error_message: null,
  metadata: {},
  provenance: { case_id: caseId },
  entities: [
    {
      id: "00000000-0000-0000-0000-000000000a03",
      analysis_run_id: "00000000-0000-0000-0000-000000000a02",
      case_id: caseId,
      canonical_id: "ENTITY-000001",
      entity_type: "email" as const,
      display_name: "shared@example.com",
      normalized_key: "shared@example.com",
      confidence: 0.98,
      support_count: 2,
      evidence_ids: [
        "00000000-0000-0000-0000-000000000a04",
        "00000000-0000-0000-0000-000000000a05",
      ],
      attributes: {},
      provenance: {
        case_id: caseId,
        extraction_ids: ["ext-1"],
        evidence_ids: [
          "00000000-0000-0000-0000-000000000a04",
          "00000000-0000-0000-0000-000000000a05",
        ],
      },
      supports: [
        {
          id: "00000000-0000-0000-0000-000000000a06",
          support_kind: "extraction",
          support_ref: "ext-1",
          label: "TEXT",
          value: "shared@example.com",
          metadata: {},
        },
      ],
      created_at: "2026-09-01T00:00:01Z",
    },
    {
      id: "00000000-0000-0000-0000-000000000a07",
      analysis_run_id: "00000000-0000-0000-0000-000000000a02",
      case_id: caseId,
      canonical_id: "ENTITY-000002",
      entity_type: "document" as const,
      display_name: "invoice.pdf",
      normalized_key: "00000000-0000-0000-0000-000000000a04",
      confidence: 0.8,
      support_count: 1,
      evidence_ids: ["00000000-0000-0000-0000-000000000a04"],
      attributes: {},
      provenance: { case_id: caseId },
      supports: [],
      created_at: "2026-09-01T00:00:01Z",
    },
  ],
  relationships: [
    {
      id: "00000000-0000-0000-0000-000000000a08",
      analysis_run_id: "00000000-0000-0000-0000-000000000a02",
      case_id: caseId,
      relationship_id: "ENTITY-000002|contains|ENTITY-000001",
      source_canonical_id: "ENTITY-000002",
      target_canonical_id: "ENTITY-000001",
      relationship_type: "contains" as const,
      confidence: 0.98,
      support_count: 1,
      explanation: "OCR/text extraction contains email entity.",
      evidence_ids: ["00000000-0000-0000-0000-000000000a04"],
      provenance: { case_id: caseId },
      supports: [],
      created_at: "2026-09-01T00:00:01Z",
    },
  ],
  graph: {
    nodes: [],
    edges: [],
    provenance: {},
    metadata: {},
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
                  ? "No entity-resolution analysis exists for this case."
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

describe("Phase 7C EntityGraphPanel", () => {
  it("renders entities with confidence", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/entities/latest")) {
          return response({
            ...entityDetail,
            graph: {
              nodes: entityDetail.entities,
              edges: entityDetail.relationships,
              provenance: {},
              metadata: {},
            },
          });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <EntityGraphPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(await screen.findByText("ENTITY-000001")).toBeInTheDocument();
    expect(screen.getByText("shared@example.com")).toBeInTheDocument();
    expect(screen.getByText(/confidence 98%/i)).toBeInTheDocument();
  });

  it("shows loading while resolving", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/entities/latest")) {
          return response({
            ...entityDetail,
            status: "RUNNING",
            entities: [],
            relationships: [],
            graph: { nodes: [], edges: [], provenance: {}, metadata: {} },
          });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <EntityGraphPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(await screen.findByText(/Loading entity graph/i)).toBeInTheDocument();
  });

  it("shows empty state on 404", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/entities/latest")) {
          return response(null, 404);
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <EntityGraphPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByText("No entities", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
  });

  it("shows error state on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/entities/latest")) {
          return response(null, 500);
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <EntityGraphPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(
      await screen.findByText("Entity graph unavailable", {}, { timeout: 5000 }),
    ).toBeInTheDocument();
  });

  it("expands provenance and relationships", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/entities/latest")) {
          return response({
            ...entityDetail,
            graph: {
              nodes: entityDetail.entities,
              edges: entityDetail.relationships,
              provenance: {},
              metadata: {},
            },
          });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <EntityGraphPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(await screen.findByText("ENTITY-000001")).toBeInTheDocument();
    await user.click(screen.getAllByText(/Provenance & relationships/i)[0]);
    expect(screen.getByText(/^Relationships$/i)).toBeInTheDocument();
    expect(screen.getByText(/extraction_ids/i)).toBeInTheDocument();
  });

  it("filters by entity type", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/entities/latest")) {
          return response({
            ...entityDetail,
            graph: {
              nodes: entityDetail.entities,
              edges: entityDetail.relationships,
              provenance: {},
              metadata: {},
            },
          });
        }
        return response({});
      }),
    );

    render(
      <TestProviders>
        <EntityGraphPanel caseId={caseId} />
      </TestProviders>,
    );

    expect(await screen.findByText("ENTITY-000001")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText(/Filter entity type/i), "email");
    expect(screen.getByText("ENTITY-000001")).toBeInTheDocument();
    expect(screen.queryByText("ENTITY-000002")).not.toBeInTheDocument();
  });
});
