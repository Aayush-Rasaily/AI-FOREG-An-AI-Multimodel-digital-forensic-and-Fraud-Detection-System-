import {
  useAnalyzeEvidenceMutation,
  useEvidenceAnalysisSummaryQuery,
  useEvidenceFindingsQuery,
  useEvidenceHeatmapsQuery,
} from "../../hooks/useForensics";
import { ApiClientError } from "../../services/api/client";
import type { EvidenceRecord } from "../../types/evidence";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { LoadingState } from "../ui/LoadingState";
import { Microscope } from "lucide-react";

interface EvidenceForensicsPanelProps {
  evidence: EvidenceRecord;
}

const severityTone: Record<string, "neutral" | "primary" | "success" | "warning" | "error"> =
  {
    INFO: "neutral",
    LOW: "primary",
    MEDIUM: "warning",
    HIGH: "error",
    CRITICAL: "error",
  };

export function EvidenceForensicsPanel({ evidence }: EvidenceForensicsPanelProps) {
  const summaryQuery = useEvidenceAnalysisSummaryQuery(evidence.id);
  const findingsQuery = useEvidenceFindingsQuery(evidence.id);
  const heatmapsQuery = useEvidenceHeatmapsQuery(evidence.id);
  const analyzeMutation = useAnalyzeEvidenceMutation(evidence.id);
  const summary = summaryQuery.data?.data;
  const findings = findingsQuery.data?.data.items ?? [];
  const status = summary?.status ?? "QUEUED";

  return (
    <div className="mt-2 rounded-lg border border-border bg-background/50 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Microscope aria-hidden="true" className="text-muted" size={14} />
          <span className="text-[11px] uppercase tracking-wider text-subtle">
            Forensic analysis
          </span>
          <Badge tone={status === "SUCCEEDED" ? "success" : status === "FAILED" ? "error" : "neutral"}>
            {status}
          </Badge>
        </div>
        <Button
          disabled={analyzeMutation.isPending || status === "RUNNING"}
          onClick={() => analyzeMutation.mutate()}
          size="sm"
          variant="secondary"
        >
          {analyzeMutation.isPending ? "Analyzing" : "Run analysis"}
        </Button>
      </div>

      {summaryQuery.isPending && <LoadingState label="Loading analysis summary" />}
      {analyzeMutation.isError && (
        <p className="mt-2 text-[11px] text-danger">
          {analyzeMutation.error instanceof ApiClientError
            ? analyzeMutation.error.message
            : "Analysis could not be started."}
        </p>
      )}

      {findingsQuery.isSuccess && findings.length === 0 && status === "SUCCEEDED" && (
        <EmptyState
          className="mt-2 min-h-24"
          description="Analysis completed without elevated forensic indicators."
          title="No findings"
        />
      )}

      {findings.length > 0 && (
        <div className="mt-3 max-h-48 space-y-1.5 overflow-y-auto">
          {findings.slice(0, 8).map((finding) => (
            <div
              className="rounded border border-border px-2 py-1.5"
              key={finding.id}
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={severityTone[finding.severity] ?? "neutral"}>
                  {finding.severity}
                </Badge>
                <span className="text-[10px] text-muted">{finding.detector}</span>
                <span className="text-[10px] text-subtle">
                  {(finding.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="mt-0.5 text-[11px] text-muted">{finding.description}</p>
            </div>
          ))}
        </div>
      )}

      {heatmapsQuery.isSuccess && heatmapsQuery.data.data.items.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1 border-t border-border pt-2">
          {heatmapsQuery.data.data.items.map((artifact) => (
            <Badge key={artifact.id} tone="info">
              {artifact.artifact_type}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
