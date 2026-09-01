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
  "neutral" | "cyan" | "green" | "amber" | "red"
> = {
  SUCCEEDED: "green",
  RUNNING: "cyan",
  QUEUED: "amber",
  FAILED: "red",
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
            className="min-h-48 rounded-lg border border-dashed border-slate-800"
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
              <span className="text-[11px] text-slate-500">
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
          <p className="mt-2 text-[11px] text-red-300">
            {analyzeMutation.error instanceof ApiClientError
              ? analyzeMutation.error.message
              : "Analysis could not be started."}
          </p>
        )}
        {summary?.error_code && summary.error_code !== "ANALYSIS_NOT_RUN" && (
          <p className="mt-2 text-[11px] text-amber-300">
            Status: {summary.error_code}
          </p>
        )}

        {showHistory && analysisQuery.isSuccess && (
          <div className="mt-3 space-y-2 border-t border-slate-800 pt-3">
            {analysisQuery.data.data.items.length === 0 ? (
              <EmptyState
                description="No forensic analysis runs have been recorded."
                title="No analysis history"
              />
            ) : (
              analysisQuery.data.data.items.map((run) => (
                <div
                  className="rounded border border-slate-800 px-2.5 py-2 text-xs text-slate-400"
                  key={run.id}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={statusTone[run.status] ?? "neutral"}>
                      {run.status}
                    </Badge>
                    <span>{run.findings_count} findings</span>
                    <span className="text-[10px] text-slate-600">
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
