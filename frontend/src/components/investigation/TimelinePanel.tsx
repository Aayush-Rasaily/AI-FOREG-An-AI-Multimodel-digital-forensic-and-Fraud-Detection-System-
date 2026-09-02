import { ChevronDown, ChevronRight, Clock3 } from "lucide-react";
import { useState } from "react";

import {
  useGenerateTimelineMutation,
  useTimelineLatestQuery,
} from "../../hooks/useTimeline";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface TimelinePanelProps {
  caseId: string;
}

function confidenceTone(confidence: number): "cyan" | "amber" | "neutral" {
  if (confidence >= 0.85) {
    return "cyan";
  }
  if (confidence >= 0.5) {
    return "amber";
  }
  return "neutral";
}

export function TimelinePanel({ caseId }: TimelinePanelProps) {
  const latestQuery = useTimelineLatestQuery(caseId);
  const generateMutation = useGenerateTimelineMutation();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const isNotFound =
    latestQuery.error instanceof ApiClientError && latestQuery.error.status === 404;
  const timeline = latestQuery.data?.data;
  const events = timeline?.events ?? [];
  const conflicts = timeline?.conflicts ?? [];
  const isGenerating =
    timeline?.status === "QUEUED" || timeline?.status === "RUNNING";

  const toggleProvenance = (eventId: string) => {
    setExpanded((current) => ({ ...current, [eventId]: !current[eventId] }));
  };

  return (
    <Panel
      description="Deterministic investigation timeline reconstructed from evidence, custody, processing, AI, fusion, and report timestamps."
      title="Investigation Timeline"
    >
      <div className="space-y-4 p-4">
        <div className="flex justify-end">
          <Button
            disabled={generateMutation.isPending || isGenerating}
            onClick={() => generateMutation.mutate({ caseId })}
            size="sm"
            variant="secondary"
          >
            {generateMutation.isPending || isGenerating
              ? "Reconstructing…"
              : "Reconstruct Timeline"}
          </Button>
        </div>

        {(latestQuery.isLoading || isGenerating) && (
          <LoadingState label="Loading timeline…" />
        )}

        {!latestQuery.isLoading && latestQuery.isError && !isNotFound && (
          <ErrorState
            description="Unable to load investigation timeline."
            title="Timeline unavailable"
          />
        )}

        {!latestQuery.isLoading && (isNotFound || events.length === 0) && !isGenerating && (
          <EmptyState
            description="Reconstruct the timeline to collect chronological events across all case evidence."
            icon={<Clock3 aria-hidden="true" size={19} />}
            title="No timeline events"
          />
        )}

        {conflicts.length > 0 && (
          <div className="space-y-2 rounded-lg border border-amber-900/50 bg-amber-950/20 p-3">
            <p className="text-xs font-medium text-amber-300">
              Timestamp conflicts ({conflicts.length})
            </p>
            {conflicts.map((conflict) => (
              <div className="text-xs text-amber-100/90" key={conflict.conflict_id}>
                <Badge tone="amber">{conflict.conflict_type.replaceAll("_", " ")}</Badge>
                <span className="ml-2">{conflict.explanation}</span>
              </div>
            ))}
          </div>
        )}

        {events.length > 0 && !isGenerating && (
          <div className="space-y-3">
            {events.map((event) => {
              const isOpen = expanded[event.event_id] ?? false;
              return (
                <div
                  className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
                  key={event.event_id}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={event.normalized_timestamp ? "cyan" : "neutral"}>
                      {event.event_type.replaceAll("_", " ")}
                    </Badge>
                    <Badge tone={confidenceTone(event.confidence)}>
                      confidence {(event.confidence * 100).toFixed(0)}%
                    </Badge>
                    <Badge tone="neutral">{event.source}</Badge>
                    {event.timezone && (
                      <span className="text-[11px] text-slate-500">{event.timezone}</span>
                    )}
                    <span className="text-[11px] text-slate-500">
                      {event.normalized_timestamp
                        ? new Date(event.normalized_timestamp).toLocaleString()
                        : "Timestamp unknown"}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-slate-300">{event.description}</p>
                  <button
                    className="mt-2 flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200"
                    onClick={() => toggleProvenance(event.event_id)}
                    type="button"
                  >
                    {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    Provenance
                  </button>
                  {isOpen && (
                    <pre className="mt-2 overflow-x-auto rounded bg-slate-900/70 p-2 font-mono text-[10px] text-slate-400">
                      {JSON.stringify(event.provenance, null, 2)}
                    </pre>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Panel>
  );
}
