import { useMemo, useState } from "react";
import { AudioLines, Sparkles, Timer, Waves } from "lucide-react";

import {
  useAnalyzeAudioMutation,
  useAudioAnalysisDetailQuery,
  useAudioAnalysisQuery,
  useAudioFindingsQuery,
} from "../../hooks/useAudioAI";
import type { EvidenceRecord } from "../../types/evidence";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface AudioAnalysisPanelProps {
  evidence?: EvidenceRecord;
  referenceOptions?: EvidenceRecord[];
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
  "synthetic_audio",
  "voice_clone",
  "deepfake_voice",
  "speaker_consistency",
  "splicing",
  "waveform",
  "spectral",
  "compression",
  "noise_consistency",
  "silence",
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

export function AudioAnalysisPanel({
  evidence,
  referenceOptions = [],
}: AudioAnalysisPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const [detectorFilter, setDetectorFilter] = useState<string>("all");
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);
  const [referenceId, setReferenceId] = useState<string>("");
  const runsQuery = useAudioAnalysisQuery(evidenceId);
  const findingsQuery = useAudioFindingsQuery(
    evidenceId,
    detectorFilter === "all" ? undefined : detectorFilter,
  );
  const analyzeMutation = useAnalyzeAudioMutation();
  const latestRun = runsQuery.data?.data.items[0];
  const detailQuery = useAudioAnalysisDetailQuery(latestRun?.id);
  const findings = findingsQuery.data?.data.items ?? [];
  const timeline = detailQuery.data?.data.timeline ?? [];
  const segments = detailQuery.data?.data.segments ?? [];
  const features = detailQuery.data?.data.features;
  const waveformArtifact = detailQuery.data?.data.artifacts.find(
    (item) => item.artifact_type === "AI_AUDIO_WAVEFORM",
  );

  const selectedSegmentData = useMemo(
    () => segments.find((segment) => segment.segment_id === selectedSegment) ?? segments[0],
    [segments, selectedSegment],
  );

  const audioMeta = latestRun?.audio ?? {};

  return (
    <Panel
      description="AI audio forensic detectors with temporal localization and classical analysis."
      title="Audio AI Analysis"
    >
      <div className="space-y-3 p-4">
        {!evidence && (
          <EmptyState
            description="Select audio evidence to run AI forensic analysis."
            title="No evidence selected"
          />
        )}

        {evidence && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              {referenceOptions.length > 0 && (
                <select
                  aria-label="Reference audio"
                  className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-300"
                  onChange={(event) => setReferenceId(event.target.value)}
                  value={referenceId}
                >
                  <option value="">No reference</option>
                  {referenceOptions
                    .filter((item) => item.id !== evidence.id)
                    .map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.original_filename}
                      </option>
                    ))}
                </select>
              )}
              <Button
                disabled={analyzeMutation.isPending}
                onClick={() =>
                  analyzeMutation.mutate({
                    evidenceId: evidence.id,
                    body: referenceId
                      ? { reference_evidence_id: referenceId }
                      : {},
                  })
                }
                size="sm"
              >
                <Sparkles aria-hidden="true" size={14} />
                Run AI audio analysis
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

            {runsQuery.isPending && <LoadingState label="Loading AI audio analysis runs" />}
            {runsQuery.isError && (
              <ErrorState
                description={
                  runsQuery.error instanceof ApiClientError
                    ? runsQuery.error.message
                    : "AI audio analysis history could not be loaded."
                }
                onRetry={() => void runsQuery.refetch()}
              />
            )}

            {latestRun && (
              <div className="rounded border border-slate-800 px-3 py-2 text-xs text-slate-400">
                <div className="flex flex-wrap items-center gap-2">
                  <AudioLines aria-hidden="true" size={14} />
                  <span>Engine v{latestRun.engine_version}</span>
                  <span>·</span>
                  <span>{latestRun.findings_count} findings</span>
                  {audioMeta.sample_rate != null && (
                    <>
                      <span>·</span>
                      <span>{String(audioMeta.sample_rate)} Hz</span>
                    </>
                  )}
                  {audioMeta.channels != null && (
                    <>
                      <span>·</span>
                      <span>{String(audioMeta.channels)} ch</span>
                    </>
                  )}
                  {audioMeta.codec != null && (
                    <>
                      <span>·</span>
                      <span>{String(audioMeta.codec)}</span>
                    </>
                  )}
                </div>
                {features && (
                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
                    <span>RMS {features.rms_energy.toFixed(4)}</span>
                    <span>ZCR {features.zero_crossing_rate.toFixed(4)}</span>
                    <span>Centroid {features.spectral_centroid_hz.toFixed(1)} Hz</span>
                  </div>
                )}
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

            {waveformArtifact && (
              <div className="rounded border border-slate-800 p-3">
                <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-300">
                  <Waves aria-hidden="true" size={14} />
                  Waveform summary available
                </div>
                <p className="text-[11px] text-slate-500">
                  Derived waveform envelope artifact: {String(waveformArtifact.id)}
                </p>
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
                        setSelectedSegment(`${entry.detector}:${index}`)
                      }
                      type="button"
                    >
                      <span>
                        {formatTimestamp(entry.start_time_ms)} –{" "}
                        {formatTimestamp(entry.end_time_ms)}
                      </span>
                      <span>{entry.description}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {segments.length > 0 && (
              <div className="rounded border border-slate-800 p-3">
                <div className="mb-2 text-xs font-medium text-slate-300">
                  Segment navigator
                </div>
                <div className="flex flex-wrap gap-1">
                  {segments.map((segment) => (
                    <button
                      key={segment.segment_id}
                      className={`rounded px-2 py-1 text-[11px] ${
                        selectedSegmentData?.segment_id === segment.segment_id
                          ? "bg-cyan-900 text-cyan-100"
                          : "bg-slate-900 text-slate-400"
                      }`}
                      onClick={() => setSelectedSegment(segment.segment_id)}
                      type="button"
                    >
                      {segment.detector}
                    </button>
                  ))}
                </div>
                {selectedSegmentData && (
                  <div className="mt-2 text-[11px] text-slate-500">
                    {formatTimestamp(selectedSegmentData.start_time_ms)} –{" "}
                    {formatTimestamp(selectedSegmentData.end_time_ms)} ·{" "}
                    {selectedSegmentData.description}
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

            {findingsQuery.isPending && <LoadingState label="Loading audio findings" />}
            {findings.length === 0 && !findingsQuery.isPending && (
              <EmptyState
                description="No audio AI findings yet for the selected detector."
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
                    {formatTimestamp(finding.temporal.start_time_ms)} –{" "}
                    {formatTimestamp(finding.temporal.end_time_ms)}
                  </p>
                )}
                {finding.limitations && (
                  <p className="mt-1 text-[10px] text-slate-600">{finding.limitations}</p>
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
