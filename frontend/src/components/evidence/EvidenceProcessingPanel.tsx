import { useEffect } from "react";
import { Play, RefreshCw } from "lucide-react";

import {
  useEvidenceArtifactsQuery,
  useEvidenceProcessingQuery,
  useProcessEvidenceMutation,
} from "../../hooks/useEvidence";
import { ApiClientError } from "../../services/api/client";
import type { EvidenceRecord, ProcessingJobStatus } from "../../types/evidence";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";

interface EvidenceProcessingPanelProps {
  evidence: EvidenceRecord;
}

const statusTone: Record<
  ProcessingJobStatus | "REGISTERED" | "READY_FOR_ANALYSIS",
  "neutral" | "cyan" | "green" | "amber" | "red"
> = {
  REGISTERED: "neutral",
  QUEUED: "amber",
  RUNNING: "cyan",
  SUCCEEDED: "green",
  READY_FOR_ANALYSIS: "green",
  FAILED: "red",
  CANCELLED: "neutral",
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function EvidenceProcessingPanel({
  evidence,
}: EvidenceProcessingPanelProps) {
  const jobsQuery = useEvidenceProcessingQuery(evidence.id);
  const artifactsQuery = useEvidenceArtifactsQuery(evidence.id);
  const processMutation = useProcessEvidenceMutation(evidence.id);
  const latestJob = jobsQuery.data?.data.items[0];
  const displayStatus = latestJob?.status || evidence.status;
  const isActive =
    latestJob?.status === "QUEUED" || latestJob?.status === "RUNNING";
  const tone =
    statusTone[displayStatus as keyof typeof statusTone] || "neutral";
  const { refetch: refetchArtifacts } = artifactsQuery;

  useEffect(() => {
    if (latestJob?.status === "SUCCEEDED") {
      void refetchArtifacts();
    }
  }, [latestJob?.status, refetchArtifacts]);

  return (
    <div className="mt-2 rounded-lg border border-slate-800 bg-slate-950/50 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-[11px] uppercase tracking-wider text-slate-600">
            Processing
          </span>
          <Badge tone={tone}>
            {displayStatus.replaceAll("_", " ")}
          </Badge>
          {latestJob?.status === "SUCCEEDED" && (
            <span className="text-[11px] text-emerald-300">
              SHA-256 verified
            </span>
          )}
        </div>
        <Button
          disabled={isActive || processMutation.isPending}
          onClick={() => processMutation.mutate()}
          size="sm"
          variant="secondary"
        >
          {processMutation.isPending || isActive ? (
            <RefreshCw aria-hidden="true" className="animate-spin" size={13} />
          ) : (
            <Play aria-hidden="true" size={13} />
          )}
          {isActive ? "Processing" : "Process evidence"}
        </Button>
      </div>

      {processMutation.isError && (
        <p className="mt-2 text-[11px] text-red-300">
          {processMutation.error instanceof ApiClientError
            ? processMutation.error.message
            : "Processing could not be started."}
        </p>
      )}
      {latestJob?.status === "FAILED" && (
        <p className="mt-2 text-[11px] text-red-300">
          {latestJob.error_message || "Processing failed safely."}
        </p>
      )}

      <div className="mt-3 border-t border-slate-800 pt-3">
        <p className="text-[11px] uppercase tracking-wider text-slate-600">
          Artifacts
        </p>
        {artifactsQuery.isPending && <LoadingState label="Loading artifacts" />}
        {artifactsQuery.isError && (
          <ErrorState
            description="Derived artifacts could not be loaded."
            onRetry={() => void artifactsQuery.refetch()}
          />
        )}
        {artifactsQuery.isSuccess &&
          (artifactsQuery.data.data.items.length === 0 ? (
            <EmptyState
              description="Artifacts will appear after processing completes."
              title="No artifacts yet"
            />
          ) : (
            <div className="mt-2 space-y-2">
              {artifactsQuery.data.data.items.map((artifact) => (
                <div
                  className="rounded border border-slate-800 px-2.5 py-2"
                  key={artifact.id}
                >
                  <div className="flex items-center justify-between gap-2">
                    <Badge tone="purple">{artifact.artifact_type}</Badge>
                    <span className="text-[10px] text-slate-600">
                      {formatBytes(artifact.file_size)} · {artifact.mime_type}
                    </span>
                  </div>
                  <p className="mt-1 break-all font-mono text-[10px] text-slate-600">
                    SHA-256: {artifact.sha256_hash}
                  </p>
                </div>
              ))}
            </div>
          ))}
      </div>
    </div>
  );
}
