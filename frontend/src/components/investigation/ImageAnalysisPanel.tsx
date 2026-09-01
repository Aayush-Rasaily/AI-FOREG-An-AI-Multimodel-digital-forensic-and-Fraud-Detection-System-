import { useMemo, useState } from "react";
import { BrainCircuit, Layers, Sparkles } from "lucide-react";

import {
  useAnalyzeImageMutation,
  useImageAnalysisQuery,
  useImageFindingsQuery,
} from "../../hooks/useImageAI";
import type { EvidenceRecord } from "../../types/evidence";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface ImageAnalysisPanelProps {
  evidence?: EvidenceRecord;
}

const severityTone: Record<string, "neutral" | "cyan" | "green" | "amber" | "red"> =
  {
    INFO: "neutral",
    LOW: "cyan",
    MEDIUM: "amber",
    HIGH: "red",
    CRITICAL: "red",
  };

const detectors = [
  "ai_generated",
  "deepfake_face",
  "manipulation",
  "fake_logo",
  "government_id",
];

export function ImageAnalysisPanel({ evidence }: ImageAnalysisPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const runsQuery = useImageAnalysisQuery(evidenceId);
  const [detectorFilter, setDetectorFilter] = useState<string>("all");
  const [showHeatmaps, setShowHeatmaps] = useState(false);
  const findingsQuery = useImageFindingsQuery(
    evidenceId,
    detectorFilter === "all" ? undefined : detectorFilter,
  );
  const analyzeMutation = useAnalyzeImageMutation();
  const latestRun = runsQuery.data?.data.items[0];
  const findings = findingsQuery.data?.data.items ?? [];

  const heatmapFindings = useMemo(
    () => findings.filter((item) => item.heatmap_artifact_id != null),
    [findings],
  );

  return (
    <Panel
      description="AI image forensic detectors with model provenance and localized regions."
      title="AI Image Analysis"
    >
      <div className="space-y-3 p-4">
        {!evidence && (
          <EmptyState
            description="Select image evidence to run AI forensic analysis."
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
                Run AI image analysis
              </Button>
              {latestRun && (
                <>
                  <Badge tone={latestRun.status === "SUCCEEDED" ? "green" : "neutral"}>
                    {latestRun.status}
                  </Badge>
                  {latestRun.latency_ms != null && (
                    <span className="text-[11px] text-slate-500">
                      {latestRun.latency_ms.toFixed(2)} ms · {latestRun.device}
                    </span>
                  )}
                </>
              )}
            </div>

            {runsQuery.isPending && <LoadingState label="Loading AI analysis runs" />}
            {runsQuery.isError && (
              <ErrorState
                description={
                  runsQuery.error instanceof ApiClientError
                    ? runsQuery.error.message
                    : "AI image analysis history could not be loaded."
                }
                onRetry={() => void runsQuery.refetch()}
              />
            )}

            {latestRun && (
              <div className="rounded border border-slate-800 px-3 py-2 text-xs text-slate-400">
                <div className="flex items-center gap-2">
                  <BrainCircuit aria-hidden="true" size={14} />
                  <span>Engine v{latestRun.engine_version}</span>
                  <span>·</span>
                  <span>{latestRun.findings_count} findings</span>
                </div>
                {Array.isArray(latestRun.metadata.detectors) && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(latestRun.metadata.detectors as Array<Record<string, unknown>>).map(
                      (entry) => (
                        <Badge key={String(entry.name)} tone="neutral">
                          {String(entry.name)} ({String(entry.model_name)})
                        </Badge>
                      ),
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] text-slate-600">Detector filter</span>
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
              <Button
                aria-pressed={showHeatmaps}
                onClick={() => setShowHeatmaps((value) => !value)}
                size="sm"
                variant={showHeatmaps ? "secondary" : "ghost"}
              >
                <Layers aria-hidden="true" size={14} />
                Heatmaps
              </Button>
            </div>

            {findingsQuery.isPending && <LoadingState label="Loading AI findings" />}
            {findingsQuery.isSuccess && findings.length === 0 && (
              <EmptyState
                description="Run AI image analysis to populate detector findings."
                title="No AI image findings"
              />
            )}

            {findings.length > 0 && (
              <div className="max-h-80 space-y-2 overflow-y-auto">
                {findings.map((finding) => (
                  <div
                    className="rounded border border-slate-800 px-2.5 py-2 text-xs"
                    key={finding.id}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={severityTone[finding.severity] ?? "neutral"}>
                        {finding.severity}
                      </Badge>
                      <Badge tone="cyan">{finding.detector}</Badge>
                      <span className="text-slate-400">
                        {(finding.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="mt-1 text-slate-300">{finding.description}</p>
                    <p className="mt-1 text-[11px] text-slate-500">
                      {finding.model_name} v{finding.model_version} ·{" "}
                      {finding.model_framework}
                    </p>
                    {finding.regions.length > 0 && (
                      <p className="mt-1 text-[10px] text-slate-600">
                        {finding.regions.length} localized region
                        {finding.regions.length === 1 ? "" : "s"}
                      </p>
                    )}
                    {showHeatmaps && finding.heatmap_artifact_id && (
                      <p className="mt-1 text-[10px] text-purple-300">
                        Heatmap artifact: {finding.heatmap_artifact_id.slice(0, 8)}…
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {showHeatmaps && heatmapFindings.length === 0 && findings.length > 0 && (
              <p className="text-[11px] text-slate-600">
                No heatmap artifacts are linked to the current findings.
              </p>
            )}

            {analyzeMutation.isError && (
              <p className="text-[11px] text-red-300">
                {analyzeMutation.error instanceof ApiClientError
                  ? analyzeMutation.error.message
                  : "AI image analysis failed."}
              </p>
            )}
          </>
        )}
      </div>
    </Panel>
  );
}
