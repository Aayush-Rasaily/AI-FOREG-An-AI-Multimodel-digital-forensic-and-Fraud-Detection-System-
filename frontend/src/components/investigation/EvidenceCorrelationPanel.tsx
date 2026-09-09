import { ChevronDown, ChevronRight, GitBranch } from "lucide-react";
import { useMemo, useState } from "react";

import {
  useCorrelationLatestQuery,
  useGenerateCorrelationMutation,
} from "../../hooks/useCorrelation";
import { ApiClientError } from "../../services/api/client";
import type { CorrelationType } from "../../types/correlation";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface EvidenceCorrelationPanelProps {
  caseId: string;
}

function scoreTone(score: number): "primary" | "warning" | "neutral" {
  if (score >= 0.9) {
    return "primary";
  }
  if (score >= 0.7) {
    return "warning";
  }
  return "neutral";
}

export function EvidenceCorrelationPanel({ caseId }: EvidenceCorrelationPanelProps) {
  const latestQuery = useCorrelationLatestQuery(caseId);
  const generateMutation = useGenerateCorrelationMutation();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [filterType, setFilterType] = useState<CorrelationType | "all">("all");

  const isNotFound =
    latestQuery.error instanceof ApiClientError && latestQuery.error.status === 404;
  const detail = latestQuery.data?.data;
  const correlations = detail?.correlations ?? [];
  const isRunning =
    detail?.status === "QUEUED" || detail?.status === "RUNNING";

  const types = useMemo(() => {
    const values = new Set(correlations.map((item) => item.correlation_type));
    return Array.from(values).sort();
  }, [correlations]);

  const visible = correlations.filter(
    (item) => filterType === "all" || item.correlation_type === filterType,
  );

  return (
    <Panel
      description="Deterministic cross-evidence relationships discovered from existing hashes, OCR, metadata, AI findings, and timeline timestamps."
      title="Evidence Correlations"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap gap-2">
            <select
              aria-label="Filter correlation type"
              className="rounded-lg border border-border-strong bg-background-offset px-2 py-1 text-xs text-foreground"
              onChange={(event) =>
                setFilterType(event.target.value as CorrelationType | "all")
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
          </div>
          <Button
            disabled={generateMutation.isPending || isRunning}
            onClick={() => generateMutation.mutate({ caseId })}
            size="sm"
            variant="secondary"
          >
            {generateMutation.isPending || isRunning
              ? "Analyzing…"
              : "Run Correlation"}
          </Button>
        </div>

        {(latestQuery.isLoading || isRunning) && (
          <LoadingState label="Loading correlations…" />
        )}

        {!latestQuery.isLoading && latestQuery.isError && !isNotFound && (
          <ErrorState
            description="Unable to load evidence correlations."
            title="Correlations unavailable"
          />
        )}

        {!latestQuery.isLoading &&
          !isRunning &&
          (isNotFound || correlations.length === 0) && (
            <EmptyState
              description="Run correlation analysis to discover relationships across case evidence."
              icon={<GitBranch aria-hidden="true" size={19} />}
              title="No correlations"
            />
          )}

        {visible.length > 0 && !isRunning && (
          <div className="space-y-3">
            {visible.map((item) => {
              const isOpen = expanded[item.correlation_id] ?? false;
              return (
                <div
                  className="rounded-lg border border-border bg-background/40 p-3"
                  key={item.correlation_id}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="primary">
                      {item.correlation_type.replaceAll("_", " ")}
                    </Badge>
                    <Badge tone={scoreTone(item.score)}>
                      score {(item.score * 100).toFixed(0)}%
                    </Badge>
                    <Badge tone={scoreTone(item.confidence)}>
                      confidence {(item.confidence * 100).toFixed(0)}%
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs text-muted">{item.explanation}</p>
                  <p className="mt-1 font-mono text-[10px] text-subtle">
                    {item.left_evidence_id} ↔ {item.right_evidence_id}
                  </p>
                  {item.supporting_entities.length > 0 && (
                    <p className="mt-1 text-[11px] text-muted">
                      Entities: {item.supporting_entities.join(", ")}
                    </p>
                  )}
                  <button
                    className="mt-2 flex items-center gap-1 text-[11px] text-muted hover:text-foreground"
                    onClick={() =>
                      setExpanded((current) => ({
                        ...current,
                        [item.correlation_id]: !current[item.correlation_id],
                      }))
                    }
                    type="button"
                  >
                    {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    Provenance
                  </button>
                  {isOpen && (
                    <pre className="mt-2 overflow-x-auto rounded bg-background-offset/70 p-2 font-mono text-[10px] text-muted">
                      {JSON.stringify(
                        {
                          provenance: item.provenance,
                          supports: item.supports,
                          findings: item.supporting_findings,
                          metadata: item.supporting_metadata,
                        },
                        null,
                        2,
                      )}
                    </pre>
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
