import { useMemo, useState } from "react";
import { BrainCircuit, FileText, Sparkles } from "lucide-react";

import {
  useAnalyzeDocumentMutation,
  useDocumentAnalysisQuery,
  useDocumentFindingsQuery,
} from "../../hooks/useDocumentAI";
import type { EvidenceRecord } from "../../types/evidence";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface DocumentAnalysisPanelProps {
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

const detectors = [
  "tampering",
  "text_consistency",
  "font_consistency",
  "layout_consistency",
  "logo",
  "metadata",
  "region_anomaly",
];

export function DocumentAnalysisPanel({ evidence }: DocumentAnalysisPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const runsQuery = useDocumentAnalysisQuery(evidenceId);
  const [detectorFilter, setDetectorFilter] = useState<string>("all");
  const findingsQuery = useDocumentFindingsQuery(
    evidenceId,
    detectorFilter === "all" ? undefined : detectorFilter,
  );
  const analyzeMutation = useAnalyzeDocumentMutation();
  const latestRun = runsQuery.data?.data.items[0];
  const findings = findingsQuery.data?.data.items ?? [];

  const detectorMetadata = useMemo(() => {
    const entries = latestRun?.metadata.detectors;
    return Array.isArray(entries) ? entries : [];
  }, [latestRun]);

  return (
    <Panel
      description="AI document forensic detectors with model provenance and localized regions."
      title="AI Document Analysis"
    >
      <div className="space-y-3 p-4">
        {!evidence && (
          <EmptyState
            description="Select document evidence to run AI forensic analysis."
            title="No evidence selected"
          />
        )}

        {evidence && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                disabled={analyzeMutation.isPending}
                onClick={() => analyzeMutation.mutate(evidence.id)}
                size="sm"
              >
                <Sparkles aria-hidden="true" size={14} />
                Run AI document analysis
              </Button>
              {latestRun && (
                <>
                  <Badge tone={latestRun.status === "SUCCEEDED" ? "success" : "neutral"}>
                    {latestRun.status}
                  </Badge>
                  {latestRun.latency_ms != null && (
                    <span className="text-[11px] text-muted">
                      {latestRun.latency_ms.toFixed(2)} ms · {latestRun.device}
                    </span>
                  )}
                </>
              )}
            </div>

            {runsQuery.isPending && (
              <LoadingState label="Loading document analysis runs" />
            )}
            {runsQuery.isError && (
              <ErrorState
                description={
                  runsQuery.error instanceof ApiClientError
                    ? runsQuery.error.message
                    : "AI document analysis history could not be loaded."
                }
                onRetry={() => void runsQuery.refetch()}
              />
            )}

            {latestRun && (
              <div className="rounded border border-border px-3 py-2 text-xs text-muted">
                <div className="flex items-center gap-2">
                  <BrainCircuit aria-hidden="true" size={14} />
                  <span>Engine v{latestRun.engine_version}</span>
                  <span>·</span>
                  <span>{latestRun.findings_count} findings</span>
                </div>
                {detectorMetadata.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {detectorMetadata.map((entry) => (
                      <Badge key={String(entry.name)} tone="neutral">
                        {String(entry.name)} ({String(entry.model_name)})
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] text-subtle">Detector filter</span>
              <Button
                onClick={() => setDetectorFilter("all")}
                size="sm"
                variant={detectorFilter === "all" ? "secondary" : "ghost"}
              >
                All
              </Button>
              {detectors.map((detector) => (
                <Button
                  key={detector}
                  onClick={() => setDetectorFilter(detector)}
                  size="sm"
                  variant={detectorFilter === detector ? "secondary" : "ghost"}
                >
                  {detector}
                </Button>
              ))}
            </div>

            {findingsQuery.isPending && (
              <LoadingState label="Loading document findings" />
            )}
            {findingsQuery.isSuccess && findings.length === 0 && (
              <EmptyState
                description="Run AI document analysis to populate detector findings."
                icon={<FileText aria-hidden="true" size={18} />}
                title="No AI document findings"
              />
            )}

            {findings.length > 0 && (
              <div className="max-h-80 space-y-2 overflow-y-auto">
                {findings.map((finding) => (
                  <div
                    className="rounded border border-border px-2.5 py-2 text-xs"
                    key={finding.id}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={severityTone[finding.severity] ?? "neutral"}>
                        {finding.severity}
                      </Badge>
                      <Badge tone="primary">{finding.detector}</Badge>
                      {finding.confidence != null && (
                        <span className="text-muted">
                          {(finding.confidence * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-muted">{finding.description}</p>
                    <p className="mt-1 text-[11px] text-muted">
                      {finding.model_name} v{finding.model_version} ·{" "}
                      {finding.model_framework} · {finding.method}
                    </p>
                    {finding.regions.length > 0 && (
                      <p className="mt-1 text-[10px] text-subtle">
                        {finding.regions.length} localized region
                        {finding.regions.length === 1 ? "" : "s"}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {analyzeMutation.isError && (
              <p className="text-[11px] text-danger">
                {analyzeMutation.error instanceof ApiClientError
                  ? analyzeMutation.error.message
                  : "AI document analysis failed."}
              </p>
            )}
          </>
        )}
      </div>
    </Panel>
  );
}
