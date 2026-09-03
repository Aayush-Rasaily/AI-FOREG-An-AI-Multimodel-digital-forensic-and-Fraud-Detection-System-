import { ChevronDown, ChevronRight, GitBranch } from "lucide-react";
import { useMemo, useState } from "react";

import {
  useEntityLatestQuery,
  useGenerateEntitiesMutation,
} from "../../hooks/useEntities";
import { ApiClientError } from "../../services/api/client";
import type { EntityType } from "../../types/entities";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface EntityGraphPanelProps {
  caseId: string;
}

function confidenceTone(confidence: number): "cyan" | "amber" | "neutral" {
  if (confidence >= 0.9) {
    return "cyan";
  }
  if (confidence >= 0.7) {
    return "amber";
  }
  return "neutral";
}

export function EntityGraphPanel({ caseId }: EntityGraphPanelProps) {
  const latestQuery = useEntityLatestQuery(caseId);
  const generateMutation = useGenerateEntitiesMutation();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [filterType, setFilterType] = useState<EntityType | "all">("all");
  const [search, setSearch] = useState("");

  const isNotFound =
    latestQuery.error instanceof ApiClientError && latestQuery.error.status === 404;
  const detail = latestQuery.data?.data;
  const entities = detail?.entities ?? [];
  const relationships = detail?.relationships ?? [];
  const isRunning = detail?.status === "QUEUED" || detail?.status === "RUNNING";

  const types = useMemo(() => {
    const values = new Set(entities.map((item) => item.entity_type));
    return Array.from(values).sort();
  }, [entities]);

  const visible = entities.filter((item) => {
    const matchesType = filterType === "all" || item.entity_type === filterType;
    const query = search.trim().toLowerCase();
    const matchesSearch =
      query.length === 0 ||
      item.display_name.toLowerCase().includes(query) ||
      item.canonical_id.toLowerCase().includes(query) ||
      item.normalized_key.toLowerCase().includes(query);
    return matchesType && matchesSearch;
  });

  const relationshipsByEntity = useMemo(() => {
    const map = new Map<string, typeof relationships>();
    for (const edge of relationships) {
      for (const key of [edge.source_canonical_id, edge.target_canonical_id]) {
        const current = map.get(key) ?? [];
        current.push(edge);
        map.set(key, current);
      }
    }
    return map;
  }, [relationships]);

  return (
    <Panel
      description="Deterministic investigation entities and relationships resolved from existing extraction, AI, fusion, correlation, and timeline outputs."
      title="Entity Graph"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap gap-2">
            <select
              aria-label="Filter entity type"
              className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200"
              onChange={(event) =>
                setFilterType(event.target.value as EntityType | "all")
              }
              value={filterType}
            >
              <option value="all">All types</option>
              {types.map((type) => (
                <option key={type} value={type}>
                  {type.replaceAll("_", " ")}
                </option>
              ))}
            </select>
            <input
              aria-label="Search entities"
              className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search entities…"
              value={search}
            />
          </div>
          <Button
            disabled={generateMutation.isPending || isRunning}
            onClick={() => generateMutation.mutate({ caseId })}
            size="sm"
            variant="secondary"
          >
            {generateMutation.isPending || isRunning
              ? "Resolving…"
              : "Resolve Entities"}
          </Button>
        </div>

        {(latestQuery.isLoading || isRunning) && (
          <LoadingState label="Loading entity graph…" />
        )}

        {!latestQuery.isLoading && latestQuery.isError && !isNotFound && (
          <ErrorState
            description="Unable to load entity resolution results."
            title="Entity graph unavailable"
          />
        )}

        {!latestQuery.isLoading &&
          !isRunning &&
          (isNotFound || entities.length === 0) && (
            <EmptyState
              description="Run entity resolution to merge identifiers into a navigable investigation graph."
              icon={<GitBranch aria-hidden="true" size={19} />}
              title="No entities"
            />
          )}

        {visible.length > 0 && !isRunning && (
          <div className="space-y-3">
            <p className="text-xs text-slate-400">
              {detail?.entity_count ?? entities.length} entities ·{" "}
              {detail?.relationship_count ?? relationships.length} relationships
            </p>
            {visible.map((item) => {
              const isOpen = expanded[item.canonical_id] ?? false;
              const edges = relationshipsByEntity.get(item.canonical_id) ?? [];
              return (
                <div
                  className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
                  key={item.canonical_id}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="cyan">{item.canonical_id}</Badge>
                    <Badge tone="neutral">
                      {item.entity_type.replaceAll("_", " ")}
                    </Badge>
                    <Badge tone={confidenceTone(item.confidence)}>
                      confidence {(item.confidence * 100).toFixed(0)}%
                    </Badge>
                    <Badge tone="neutral">
                      support {item.support_count}
                    </Badge>
                    <span className="text-sm text-slate-100">
                      {item.display_name}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-slate-400">
                    Evidence: {item.evidence_ids.length} · Relationships:{" "}
                    {edges.length}
                  </p>
                  <button
                    className="mt-2 inline-flex items-center gap-1 text-xs text-cyan-300"
                    onClick={() =>
                      setExpanded((current) => ({
                        ...current,
                        [item.canonical_id]: !isOpen,
                      }))
                    }
                    type="button"
                  >
                    {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    Provenance & relationships
                  </button>
                  {isOpen && (
                    <div className="mt-2 space-y-2 text-xs text-slate-300">
                      <div>
                        <p className="mb-1 font-medium text-slate-200">
                          Relationships
                        </p>
                        {edges.length === 0 ? (
                          <p className="text-slate-500">No relationships</p>
                        ) : (
                          <ul className="space-y-1">
                            {edges.map((edge) => (
                              <li key={edge.relationship_id}>
                                {edge.source_canonical_id} —{" "}
                                {edge.relationship_type.replaceAll("_", " ")} →{" "}
                                {edge.target_canonical_id} (
                                {(edge.confidence * 100).toFixed(0)}%)
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                      <div>
                        <p className="mb-1 font-medium text-slate-200">
                          Supporting evidence
                        </p>
                        <p>
                          {item.evidence_ids.length > 0
                            ? item.evidence_ids.join(", ")
                            : "None"}
                        </p>
                      </div>
                      <pre className="overflow-x-auto rounded bg-slate-900 p-2 text-[11px] text-slate-400">
                        {JSON.stringify(item.provenance, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Panel>
  );
}
