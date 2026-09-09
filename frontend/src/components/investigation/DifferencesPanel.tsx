import { useState } from "react";
import { Columns2 } from "lucide-react";

import { useEvidenceDifferencesQuery } from "../../hooks/useComparison";
import type { EvidenceRecord } from "../../types/evidence";
import type { Difference } from "../../types/comparison";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface DifferencesPanelProps {
  evidence?: EvidenceRecord;
}

const severityTone: Record<string, "neutral" | "primary" | "success" | "warning" | "error"> =
  {
    INFO: "neutral",
    LOW: "primary",
    MEDIUM: "warning",
    HIGH: "error",
    CRITICAL: "error",
  };

export function DifferencesPanel({ evidence }: DifferencesPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const differencesQuery = useEvidenceDifferencesQuery(evidenceId);
  const [activeIndex, setActiveIndex] = useState(0);
  const differences = differencesQuery.data?.data.items ?? [];
  const active: Difference | undefined = differences[activeIndex];

  return (
    <Panel title="Comparison differences">
      <div className="p-4">
        {!evidenceId && (
          <EmptyState
            className="min-h-48 rounded-lg border border-dashed border-border"
            description="Select evidence to review localized comparison differences."
            icon={<Columns2 aria-hidden="true" size={19} />}
            title="No evidence selected"
          />
        )}
        {evidenceId && differencesQuery.isPending && (
          <LoadingState label="Loading differences" />
        )}
        {evidenceId && differencesQuery.isError && (
          <ErrorState
            description="Comparison differences could not be loaded."
            onRetry={() => void differencesQuery.refetch()}
          />
        )}
        {evidenceId && differencesQuery.isSuccess && differences.length === 0 && (
          <EmptyState
            description="Run a reference comparison to populate structured differences."
            title="No differences"
          />
        )}
        {differences.length > 0 && (
          <div className="space-y-2">
            <div className="max-h-48 space-y-1 overflow-y-auto">
              {differences.map((difference, index) => (
                <button
                  className={`w-full rounded border px-2 py-1.5 text-left transition-colors ${
                    index === activeIndex
                      ? "border-primary/40 bg-primary/10"
                      : "border-border hover:border-border-strong"
                  }`}
                  key={difference.id}
                  onClick={() => setActiveIndex(index)}
                  type="button"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={severityTone[difference.severity] ?? "neutral"}>
                      {difference.severity}
                    </Badge>
                    <span className="text-[10px] text-muted">
                      {difference.difference_type}
                    </span>
                  </div>
                  <p className="mt-0.5 text-[11px] text-muted">
                    {difference.description}
                  </p>
                </button>
              ))}
            </div>
            {active && (
              <div className="grid gap-2 rounded border border-border p-2 sm:grid-cols-2">
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-subtle">
                    Original
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {active.original_value ?? "—"}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-subtle">
                    Submitted
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {active.submitted_value ?? "—"}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
        <p className="mt-3 text-[10px] text-subtle">
          Differences describe what changed, not fake/real verdicts.
        </p>
      </div>
    </Panel>
  );
}
