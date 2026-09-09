import { useState } from "react";
import { Activity, Layers3, PlayCircle } from "lucide-react";

import {
  useAnalyzeEvidenceMutation,
  useEvidenceAnalysisQuery,
  useEvidenceAnalysisSummaryQuery,
} from "../../hooks/useForensics";
import type { EvidenceRecord } from "../../types/evidence";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface AnalysisPanelProps {
  evidence?: EvidenceRecord;
}

const statusTone: Record<
  string,
  "neutral" | "primary" | "success" | "warning" | "error"
> = {
  SUCCEEDED: "success",
  RUNNING: "primary",
  QUEUED: "warning",
  FAILED: "error",
};

export function AnalysisPanel({ evidence }: AnalysisPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const enabled = Boolean(evidenceId);
  const analysisQuery = useEvidenceAnalysisQuery(evidenceId);
  const summaryQuery = useEvidenceAnalysisSummaryQuery(evidenceId);
  const analyzeMutation = useAnalyzeEvidenceMutation(evidenceId);
  const [showHistory, setShowHistory] = useState(false);
  const latestRun = analysisQuery.data?.data.items[0];
  const summary = summaryQuery.data?.data;
  const status = latestRun?.status ?? summary?.status ?? "QUEUED";

  if (!enabled) {
    return (
      <Panel title="Analysis panel">
        <div className="p-4">
          <EmptyState
            className="min-h-48 rounded-lg border border-dashed border-border"
            description="Select evidence to run deterministic forensic analysis."
            icon={<Layers3 aria-hidden="true" size={19} />}
            title="No evidence selected"
          />
        </div>
      </Panel>
    );
  }

  return (
    <Panel title="Analysis panel">
      <div className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge tone={statusTone[status] ?? "neutral"}>{status}</Badge>
            {summary && summary.findings_count > 0 && (
              <span className="text-[11px] text-muted">
                {summary.findings_count} findings
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              disabled={analyzeMutation.isPending || status === "RUNNING"}
              onClick={() => analyzeMutation.mutate()}
              size="sm"
              variant="secondary"
            >
              <PlayCircle aria-hidden="true" size={14} />
              {analyzeMutation.isPending ? "Starting" : "Run analysis"}
            </Button>
            <Button
              onClick={() => setShowHistory((value) => !value)}
              size="sm"
              variant="ghost"
            >
              <Activity aria-hidden="true" size={14} />
              {showHistory ? "Hide history" : "View history"}
            </Button>
          </div>
        </div>

        {analysisQuery.isPending && <LoadingState label="Loading analysis" />}
        {analysisQuery.isError && (
          <ErrorState
            description="Analysis history could not be loaded."
            onRetry={() => void analysisQuery.refetch()}
          />
        )}
        {analyzeMutation.isError && (
          <p className="mt-2 text-[11px] text-danger">
            {analyzeMutation.error instanceof ApiClientError
              ? analyzeMutation.error.message
              : "Analysis could not be started."}
          </p>
        )}
        {summary?.error_code && summary.error_code !== "ANALYSIS_NOT_RUN" && (
          <p className="mt-2 text-[11px] text-warning">
            Status: {summary.error_code}
          </p>
        )}

        {showHistory && analysisQuery.isSuccess && (
          <div className="mt-3 space-y-2 border-t border-border pt-3">
            {analysisQuery.data.data.items.length === 0 ? (
              <EmptyState
                description="No forensic analysis runs have been recorded."
                title="No analysis history"
              />
            ) : (
              analysisQuery.data.data.items.map((run) => (
                <div
                  className="rounded border border-border px-2.5 py-2 text-xs text-muted"
                  key={run.id}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={statusTone[run.status] ?? "neutral"}>
                      {run.status}
                    </Badge>
                    <span>{run.findings_count} findings</span>
                    <span className="text-[10px] text-subtle">
                      Engine v{run.engine_version}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}
