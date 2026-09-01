import { useMemo, useState } from "react";
import { Clapperboard, Film, Sparkles, Timer } from "lucide-react";

import {
  useAnalyzeVideoMutation,
  useVideoAnalysisDetailQuery,
  useVideoAnalysisQuery,
  useVideoFindingsQuery,
} from "../../hooks/useVideoAI";
import type { EvidenceRecord } from "../../types/evidence";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface VideoAnalysisPanelProps {
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
  "deepfake",
  "synthetic_video",
  "temporal",
  "frame_manipulation",
  "face_consistency",
  "compression",
  "metadata",
];

function formatTimestamp(ms: number | null | undefined): string {
  if (ms == null) return "—";
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remSeconds = seconds % 60;
  const remMs = ms % 1000;
  return `${minutes}:${String(remSeconds).padStart(2, "0")}.${String(remMs).padStart(3, "0")}`;
}

export function VideoAnalysisPanel({ evidence }: VideoAnalysisPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const runsQuery = useVideoAnalysisQuery(evidenceId);
  const [detectorFilter, setDetectorFilter] = useState<string>("all");
  const [selectedFrame, setSelectedFrame] = useState<number | null>(null);
  const findingsQuery = useVideoFindingsQuery(
    evidenceId,
    detectorFilter === "all" ? undefined : detectorFilter,
  );
  const analyzeMutation = useAnalyzeVideoMutation();
  const latestRun = runsQuery.data?.data.items[0];
  const detailQuery = useVideoAnalysisDetailQuery(latestRun?.id);
  const findings = findingsQuery.data?.data.items ?? [];
  const frames = detailQuery.data?.data.frames ?? [];
  const timeline = detailQuery.data?.data.timeline ?? [];

  const selectedFrameData = useMemo(
    () => frames.find((frame) => frame.frame_number === selectedFrame) ?? frames[0],
    [frames, selectedFrame],
  );

  return (
    <Panel
      description="AI video forensic detectors with temporal localization and frame sampling."
      title="Video AI Analysis"
    >
      <div className="space-y-3 p-4">
        {!evidence && (
          <EmptyState
            description="Select video evidence to run AI forensic analysis."
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
                Run AI video analysis
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

            {runsQuery.isPending && <LoadingState label="Loading AI video analysis runs" />}
            {runsQuery.isError && (
              <ErrorState
                description={
                  runsQuery.error instanceof ApiClientError
                    ? runsQuery.error.message
                    : "AI video analysis history could not be loaded."
                }
                onRetry={() => void runsQuery.refetch()}
              />
            )}

            {latestRun && (
              <div className="rounded border border-slate-800 px-3 py-2 text-xs text-slate-400">
                <div className="flex items-center gap-2">
                  <Clapperboard aria-hidden="true" size={14} />
                  <span>Engine v{latestRun.engine_version}</span>
                  <span>·</span>
                  <span>{latestRun.findings_count} findings</span>
                  {latestRun.video?.duration_ms != null && (
                    <>
                      <span>·</span>
                      <span>
                        {formatTimestamp(Number(latestRun.video.duration_ms))} duration
                      </span>
                    </>
                  )}
                </div>
                {Array.isArray(latestRun.metadata.detectors) && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(latestRun.metadata.detectors as Array<Record<string, unknown>>).map(
                      (entry) => (
                        <Badge key={String(entry.name)} tone="neutral">
                          {String(entry.name)} ({String(entry.method ?? "classical")})
                        </Badge>
                      ),
                    )}
                  </div>
                )}
              </div>
            )}

            {timeline.length > 0 && (
              <div className="rounded border border-slate-800 p-3">
                <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-300">
                  <Timer aria-hidden="true" size={14} />
                  Timeline
                </div>
                <div className="space-y-2">
                  {timeline.map((entry, index) => (
                    <button
                      key={`${entry.detector}-${index}`}
                      className="flex w-full items-start justify-between rounded border border-slate-800 px-2 py-1 text-left text-[11px] text-slate-400 hover:border-cyan-700"
                      onClick={() =>
                        setSelectedFrame(entry.start_frame ?? selectedFrame)
                      }
                      type="button"
                    >
                      <span>
                        {formatTimestamp(entry.start_timestamp_ms)} –{" "}
                        {formatTimestamp(entry.end_timestamp_ms)}
                      </span>
                      <span>{entry.description}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {frames.length > 0 && (
              <div className="rounded border border-slate-800 p-3">
                <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-300">
                  <Film aria-hidden="true" size={14} />
                  Frame navigator
                </div>
                <div className="flex flex-wrap gap-1">
                  {frames.map((frame) => (
                    <button
                      key={frame.frame_id || frame.frame_number}
                      className={`rounded px-2 py-1 text-[11px] ${
                        selectedFrameData?.frame_number === frame.frame_number
                          ? "bg-cyan-900 text-cyan-100"
                          : "bg-slate-900 text-slate-400"
                      }`}
                      onClick={() => setSelectedFrame(frame.frame_number)}
                      type="button"
                    >
                      #{frame.frame_number}
                    </button>
                  ))}
                </div>
                {selectedFrameData && (
                  <div className="mt-2 text-[11px] text-slate-500">
                    Frame {selectedFrameData.frame_number} ·{" "}
                    {formatTimestamp(selectedFrameData.timestamp_ms)}
                  </div>
                )}
              </div>
            )}

            <div className="flex flex-wrap gap-1">
              <Button
                onClick={() => setDetectorFilter("all")}
                size="sm"
                variant={detectorFilter === "all" ? "primary" : "ghost"}
              >
                All detectors
              </Button>
              {detectors.map((detector) => (
                <Button
                  key={detector}
                  onClick={() => setDetectorFilter(detector)}
                  size="sm"
                  variant={detectorFilter === detector ? "primary" : "ghost"}
                >
                  {detector}
                </Button>
              ))}
            </div>

            {findingsQuery.isPending && <LoadingState label="Loading video findings" />}
            {findings.length === 0 && !findingsQuery.isPending && (
              <EmptyState
                description="No video AI findings yet for the selected detector."
                title="No findings"
              />
            )}
            {findings.map((finding) => (
              <div
                key={finding.id}
                className="rounded border border-slate-800 px-3 py-2 text-xs"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={severityTone[finding.severity] ?? "neutral"}>
                    {finding.severity}
                  </Badge>
                  <Badge tone="neutral">{finding.category}</Badge>
                  <Badge tone="neutral">{finding.method}</Badge>
                  {finding.confidence != null && (
                    <span className="text-slate-500">
                      {(finding.confidence * 100).toFixed(1)}%
                    </span>
                  )}
                  {finding.confidence == null && (
                    <span className="text-slate-500">Unavailable</span>
                  )}
                </div>
                <p className="mt-2 text-slate-200">{finding.description}</p>
                <p className="mt-1 text-slate-500">{finding.explanation}</p>
                {finding.temporal && (
                  <p className="mt-1 text-cyan-400">
                    {formatTimestamp(finding.temporal.start_timestamp_ms)} –{" "}
                    {formatTimestamp(finding.temporal.end_timestamp_ms)}
                  </p>
                )}
                <p className="mt-1 text-[10px] text-slate-600">
                  {finding.model_name} v{finding.model_version}
                </p>
              </div>
            ))}
          </>
        )}
      </div>
    </Panel>
  );
}
