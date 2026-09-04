import { useMemo, useState } from "react";
import { GitBranch, Network } from "lucide-react";

import {
  useBuildKnowledgeGraphMutation,
  useGraphNeighborsQuery,
  useKnowledgeGraphQuery,
} from "../../hooks/useKnowledgeGraph";
import { ApiClientError } from "../../services/api/client";
import type {
  GraphEntity,
  GraphRelationship,
} from "../../types/knowledgeGraph";
import { EntityInspector } from "./EntityInspector";
import { GraphFilters } from "./GraphFilters";
import { GraphLegend, nodeColor } from "./GraphLegend";
import { RelationshipInspector } from "./RelationshipInspector";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface KnowledgeGraphPanelProps {
  caseId: string;
}

function layoutNodes(entities: GraphEntity[], width: number, height: number) {
  const n = Math.max(entities.length, 1);
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) * 0.36;
  return entities.map((entity, index) => {
    const angle = (2 * Math.PI * index) / n - Math.PI / 2;
    return {
      ...entity,
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  });
}

export function KnowledgeGraphPanel({ caseId }: KnowledgeGraphPanelProps) {
  const graphQuery = useKnowledgeGraphQuery(caseId);
  const buildMutation = useBuildKnowledgeGraphMutation(caseId);
  const [search, setSearch] = useState("");
  const [entityType, setEntityType] = useState("all");
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [selectedEntityKey, setSelectedEntityKey] = useState<string | null>(
    null,
  );
  const [selectedRelationship, setSelectedRelationship] =
    useState<GraphRelationship | null>(null);

  const isNotFound =
    graphQuery.error instanceof ApiClientError &&
    graphQuery.error.status === 404;
  const graph = graphQuery.data?.data;
  const entities = graph?.entities ?? [];
  const relationships = graph?.relationships ?? [];

  const neighborsQuery = useGraphNeighborsQuery(selectedEntityId);

  const types = useMemo(
    () =>
      Array.from(new Set(entities.map((item) => item.entity_type))).sort(),
    [entities],
  );

  const visible = entities.filter((item) => {
    const matchesType =
      entityType === "all" || item.entity_type === entityType;
    const query = search.trim().toLowerCase();
    const matchesSearch =
      query.length === 0 ||
      item.display_name.toLowerCase().includes(query) ||
      item.entity_key.toLowerCase().includes(query) ||
      item.normalized_key.toLowerCase().includes(query);
    return matchesType && matchesSearch;
  });

  const width = 640;
  const height = 360;
  const laidOut = layoutNodes(visible.slice(0, 40), width, height);
  const byKey = new Map(laidOut.map((item) => [item.entity_key, item]));
  const visibleKeys = new Set(laidOut.map((item) => item.entity_key));
  const visibleEdges = relationships.filter(
    (edge) =>
      visibleKeys.has(edge.source_entity_key) &&
      visibleKeys.has(edge.target_entity_key),
  );

  const selectedFallback =
    entities.find((item) => item.id === selectedEntityId) ??
    entities.find((item) => item.entity_key === selectedEntityKey) ??
    null;

  return (
    <div className="space-y-4">
      <Panel
        description="Deterministic knowledge graph built from extraction, OCR, AI findings, timeline, correlation, and fusion outputs — without re-running models."
        title="Knowledge Graph"
      >
        <div className="space-y-4 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              {graph ? (
                <>
                  <Badge tone="cyan">{graph.status}</Badge>
                  <Badge tone="neutral">{graph.entity_count} entities</Badge>
                  <Badge tone="neutral">
                    {graph.relationship_count} relationships
                  </Badge>
                </>
              ) : (
                <Badge tone="neutral">Not built</Badge>
              )}
            </div>
            <Button
              disabled={buildMutation.isPending}
              onClick={() => buildMutation.mutate()}
              size="sm"
            >
              <Network size={14} /> Build graph
            </Button>
          </div>

          <GraphFilters
            entityType={entityType}
            onSearchChange={setSearch}
            onTypeChange={setEntityType}
            search={search}
            types={types}
          />

          {graphQuery.isLoading ? (
            <LoadingState label="Loading knowledge graph" />
          ) : null}
          {graphQuery.isError && !isNotFound ? (
            <ErrorState
              description="Unable to load the knowledge graph."
              title="Graph unavailable"
            />
          ) : null}
          {buildMutation.isError ? (
            <ErrorState
              description="Knowledge graph build failed."
              title="Build error"
            />
          ) : null}

          {(isNotFound || (!graph && !graphQuery.isLoading)) &&
          !buildMutation.isPending ? (
            <EmptyState
              description="Build the knowledge graph to resolve entities and relationships for this case."
              title="No knowledge graph"
            />
          ) : null}

          {graph && !visible.length ? (
            <EmptyState
              description="No entities match the current filters."
              title="No matches"
            />
          ) : null}

          {laidOut.length ? (
            <svg
              aria-label="Knowledge graph visualization"
              className="w-full rounded-lg border border-slate-800 bg-slate-950/50"
              height={height}
              role="img"
              viewBox={`0 0 ${width} ${height}`}
            >
              {visibleEdges.map((edge) => {
                const source = byKey.get(edge.source_entity_key);
                const target = byKey.get(edge.target_entity_key);
                if (!source || !target) return null;
                return (
                  <g key={edge.id}>
                    <line
                      opacity={0.45}
                      stroke="#64748b"
                      strokeWidth={1 + edge.confidence}
                      x1={source.x}
                      x2={target.x}
                      y1={source.y}
                      y2={target.y}
                    />
                    <text
                      className="cursor-pointer fill-slate-500 text-[8px]"
                      onClick={() => setSelectedRelationship(edge)}
                      textAnchor="middle"
                      x={(source.x + target.x) / 2}
                      y={(source.y + target.y) / 2 - 4}
                    >
                      {edge.relationship_type}
                    </text>
                  </g>
                );
              })}
              {laidOut.map((node) => (
                <g
                  className="cursor-pointer"
                  key={node.id}
                  onClick={() => {
                    setSelectedEntityId(node.id);
                    setSelectedEntityKey(node.entity_key);
                  }}
                >
                  <circle
                    cx={node.x}
                    cy={node.y}
                    fill={nodeColor(node.entity_type)}
                    opacity={0.9}
                    r={10}
                    stroke={
                      node.id === selectedEntityId ? "#f8fafc" : "#0f172a"
                    }
                    strokeWidth={node.id === selectedEntityId ? 2 : 1}
                  />
                  <text
                    className="fill-slate-200 text-[9px]"
                    textAnchor="middle"
                    x={node.x}
                    y={node.y + 22}
                  >
                    {node.display_name.slice(0, 18)}
                  </text>
                </g>
              ))}
            </svg>
          ) : null}

          {neighborsQuery.data?.data ? (
            <div className="rounded-lg border border-slate-800 p-3 text-xs text-slate-400">
              <div className="mb-2 flex items-center gap-2 text-slate-300">
                <GitBranch size={14} /> Neighbors
              </div>
              <ul className="space-y-1">
                {neighborsQuery.data.data.neighbors.map((item) => (
                  <li key={item.id}>
                    <button
                      className="text-left hover:text-cyan-300"
                      onClick={() => {
                        setSelectedEntityId(item.id);
                        setSelectedEntityKey(item.entity_key);
                      }}
                      type="button"
                    >
                      {item.entity_type}: {item.display_name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-3">
        <EntityInspector
          entityId={selectedEntityId}
          fallback={selectedFallback}
        />
        <RelationshipInspector relationship={selectedRelationship} />
        <GraphLegend />
      </div>
    </div>
  );
}
