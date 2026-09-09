import { useState } from "react";
import { ListChecks, MapPin } from "lucide-react";

import { FindingCard } from "../findings/FindingCard";
import {
  useEvidenceFindingsQuery,
  useEvidenceHeatmapsQuery,
} from "../../hooks/useForensics";
import type { EvidenceRecord } from "../../types/evidence";
import type { ForensicFinding } from "../../types/forensics";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface FindingsPanelProps {
  evidence?: EvidenceRecord;
}

const severityTone: Record<
  string,
  "neutral" | "primary" | "success" | "warning" | "error"
> = {
  INFO: "neutral",
  LOW: "primary",
  MEDIUM: "warning",
  HIGH: "error",
  CRITICAL: "error",
};

export function FindingsPanel({ evidence }: FindingsPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const findingsQuery = useEvidenceFindingsQuery(evidenceId);
  const heatmapsQuery = useEvidenceHeatmapsQuery(evidenceId);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);
  const [showHeatmaps, setShowHeatmaps] = useState(false);
  const findings = findingsQuery.data?.data.items ?? [];
  const selectedFinding = findings.find((item) => item.id === selectedFindingId);

  return (
    <Panel
      description="Only engine-backed forensic observations are shown."
      title="Findings"
    >
      <div className="space-y-3 p-4">
        {!evidence && <FindingCard />}

        {evidence && findingsQuery.isPending && (
          <LoadingState label="Loading findings" />
        )}
        {evidence && findingsQuery.isError && (
          <ErrorState
            description="Forensic findings could not be loaded."
            onRetry={() => void findingsQuery.refetch()}
          />
        )}

        {evidence && findingsQuery.isSuccess && findings.length === 0 && (
          <EmptyState
            description="Run forensic analysis to populate deterministic findings."
            title="No findings recorded"
          />
        )}

        {evidence && findings.length > 0 && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                aria-pressed={showHeatmaps}
                onClick={() => setShowHeatmaps((value) => !value)}
                size="sm"
                variant={showHeatmaps ? "secondary" : "ghost"}
              >
                Heatmaps
              </Button>
              {heatmapsQuery.isSuccess && showHeatmaps && (
                <div className="flex flex-wrap gap-1">
                  {heatmapsQuery.data.data.items.map((artifact) => (
                    <Badge key={artifact.id} tone="info">
                      {artifact.artifact_type}
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="max-h-80 space-y-2 overflow-y-auto">
              {findings.map((finding) => (
                <button
                  className={`w-full rounded border px-2 py-2 text-left transition ${
                    selectedFindingId === finding.id
                      ? "border-primary-strong bg-primary-soft"
                      : "border-border hover:border-border-strong"
                  }`}
                  key={finding.id}
                  onClick={() => setSelectedFindingId(finding.id)}
                  type="button"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={severityTone[finding.severity] ?? "neutral"}>
                      {finding.severity}
                    </Badge>
                    <span className="text-xs text-muted">{finding.detector}</span>
                    <span className="text-[10px] text-muted">
                      {(finding.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted">{finding.description}</p>
                </button>
              ))}
            </div>

            {selectedFinding && (
              <FindingDetail finding={selectedFinding} />
            )}
          </>
        )}

        <div className="flex items-center gap-2 text-[11px] text-subtle">
          <ListChecks aria-hidden="true" size={14} />
          Findings describe forensic evidence, not authenticity verdicts.
        </div>
      </div>
    </Panel>
  );
}

function FindingDetail({ finding }: { finding: ForensicFinding }) {
  return (
    <div className="rounded-lg border border-border bg-background/40 p-3">
      <FindingCard finding={finding} />
      {finding.regions.length > 0 && (
        <div className="mt-3 border-t border-border pt-3">
          <p className="mb-2 flex items-center gap-1 text-[11px] uppercase tracking-wider text-subtle">
            <MapPin aria-hidden="true" size={12} />
            Localization
          </p>
          <div className="space-y-1">
            {finding.regions.map((region, index) => (
              <p className="text-[11px] text-muted" key={`${finding.id}-${index}`}>
                x={region.x.toFixed(1)}, y={region.y.toFixed(1)}, w=
                {region.width.toFixed(1)}, h={region.height.toFixed(1)}
                {region.page_number !== null && ` · page ${region.page_number}`}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
