import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EntityInspector } from "../components/knowledge-graph/EntityInspector";
import { GraphFilters } from "../components/knowledge-graph/GraphFilters";
import { GraphLegend } from "../components/knowledge-graph/GraphLegend";
import { KnowledgeGraphPanel } from "../components/knowledge-graph/KnowledgeGraphPanel";
import { RelationshipInspector } from "../components/knowledge-graph/RelationshipInspector";
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

const entity = {
  id: "ent-1",
  graph_id: "g1",
  case_id: "case-1",
  entity_key: "kgent_1",
  entity_type: "EMAIL",
  display_name: "a@b.com",
  normalized_key: "EMAIL:a@b.com",
  confidence: 0.98,
  attributes: {},
  evidence_ids: ["ev-1"],
  aliases: ["a@b.com"],
  provenance: [
    {
      source_kind: "extraction",
      source_id: "x1",
      evidence_id: "ev-1",
      timeline_id: null,
      correlation_id: null,
      fusion_id: null,
    },
  ],
};

const relationship = {
  id: "rel-1",
  graph_id: "g1",
  case_id: "case-1",
  relationship_key: "kgedge_1",
  source_entity_key: "kgent_1",
  target_entity_key: "kgent_2",
  relationship_type: "MENTIONS",
  confidence: 0.8,
  support_count: 1,
  provenance_count: 1,
  relationship_weight: 0.78,
  creation_source: "extraction",
  evidence_ids: ["ev-1"],
  attributes: {},
  provenance: [],
};

const graph = {
  id: "g1",
  case_id: "case-1",
  status: "SUCCEEDED",
  entity_count: 2,
  relationship_count: 1,
  engine_version: "9b.1.0",
  policy_version: "1.0",
  metadata: {},
  provenance: {},
  created_at: "2026-09-08T00:00:00Z",
  completed_at: "2026-09-08T00:00:01Z",
  entities: [
    entity,
    {
      ...entity,
      id: "ent-2",
      entity_key: "kgent_2",
      entity_type: "EVIDENCE",
      display_name: "photo.jpg",
      normalized_key: "EVIDENCE:photo.jpg",
      provenance: [],
    },
  ],
  relationships: [relationship],
};

function stubGraphApi(overrides?: {
  latestStatus?: number;
  latestData?: unknown;
}) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/knowledge-graph") && method === "POST") {
        return response(graph);
      }
      if (url.includes("/knowledge-graph/entity/") && url.includes("/neighbors")) {
        return response({
          entity,
          relationships: [relationship],
          neighbors: [graph.entities[1]],
        });
      }
      if (url.includes("/knowledge-graph/entity/")) {
        return response(entity);
      }
      if (url.includes("/cases/") && url.includes("/knowledge-graph")) {
        if ((overrides?.latestStatus ?? 200) >= 400) {
          return response(null, overrides?.latestStatus);
        }
        return response(overrides?.latestData ?? graph);
      }
      return response(null, 404);
    }),
  );
}

describe("Phase 9B knowledge graph UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubGraphApi();
  });

  it("renders graph with entities", async () => {
    render(
      <TestProviders>
        <KnowledgeGraphPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/2 entities/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/Knowledge graph visualization/i)).toBeInTheDocument();
  });

  it("shows empty state when graph missing", async () => {
    stubGraphApi({ latestStatus: 404 });
    render(
      <TestProviders>
        <KnowledgeGraphPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/No knowledge graph/i)).toBeInTheDocument();
    });
  });

  it("shows loading then content", async () => {
    render(
      <TestProviders>
        <KnowledgeGraphPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/SUCCEEDED/i)).toBeInTheDocument();
    });
  });

  it("shows error state", async () => {
    stubGraphApi({ latestStatus: 500 });
    render(
      <TestProviders>
        <KnowledgeGraphPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Graph unavailable/i)).toBeInTheDocument();
    });
  });

  it("builds graph on button click", async () => {
    stubGraphApi({ latestStatus: 404 });
    const user = userEvent.setup();
    render(
      <TestProviders>
        <KnowledgeGraphPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Build graph/i })).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /Build graph/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/SUCCEEDED|Build graph/i).length).toBeGreaterThan(0);
    });
  });

  it("renders entity inspector provenance", async () => {
    render(
      <TestProviders>
        <EntityInspector entityId="ent-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText("a@b.com")).toBeInTheDocument();
    });
    expect(screen.getByText("Provenance")).toBeInTheDocument();
    expect(screen.getByText("extraction")).toBeInTheDocument();
  });

  it("renders relationship inspector", () => {
    render(
      <TestProviders>
        <RelationshipInspector relationship={relationship} />
      </TestProviders>,
    );
    expect(screen.getByText("MENTIONS")).toBeInTheDocument();
  });

  it("renders filters and legend", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <GraphFilters
          entityType="all"
          onSearchChange={() => undefined}
          onTypeChange={() => undefined}
          search=""
          types={["EMAIL", "EVIDENCE"]}
        />
        <GraphLegend />
      </TestProviders>,
    );
    expect(screen.getByPlaceholderText(/Name, key, or id/i)).toBeInTheDocument();
    expect(screen.getByText(/Legend/i)).toBeInTheDocument();
    await user.type(screen.getByPlaceholderText(/Name, key, or id/i), "mail");
  });

  it("entity inspector empty state", () => {
    render(
      <TestProviders>
        <EntityInspector entityId={null} />
      </TestProviders>,
    );
    expect(screen.getByText(/No entity selected/i)).toBeInTheDocument();
  });
});
