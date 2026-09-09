import { ChevronDown, ChevronRight, Clock3, Search } from "lucide-react";
import { useMemo, useState } from "react";

import {
  useGenerateTimelineMutation,
  useTimelineLatestQuery,
} from "../../hooks/useTimeline";
import { ApiClientError } from "../../services/api/client";
import { InteractiveTimelineViz } from "../viz/InteractiveTimelineViz";
import { WorkspacePanelChrome } from "../workspace/WorkspacePanelChrome";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";

interface TimelinePanelProps {
  caseId: string;
}

function confidenceTone(confidence: number): "primary" | "warning" | "neutral" {
  if (confidence >= 0.85) {
    return "primary";
  }
  if (confidence >= 0.5) {
    return "warning";
  }
  return "neutral";
}

export function TimelinePanel({ caseId }: TimelinePanelProps) {
  const latestQuery = useTimelineLatestQuery(caseId);
  const generateMutation = useGenerateTimelineMutation();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [collapsedDays, setCollapsedDays] = useState<Record<string, boolean>>(
    {},
  );
  const [query, setQuery] = useState("");
  const [jumpDate, setJumpDate] = useState("");
  const [zoom, setZoom] = useState<"comfortable" | "compact">("comfortable");

  const isNotFound =
    latestQuery.error instanceof ApiClientError &&
    latestQuery.error.status === 404;
  const timeline = latestQuery.data?.data;
  const events = timeline?.events ?? [];
  const conflicts = timeline?.conflicts ?? [];
  const isGenerating =
    timeline?.status === "QUEUED" || timeline?.status === "RUNNING";

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return events.filter((event) => {
      if (
        jumpDate &&
        event.normalized_timestamp &&
        !event.normalized_timestamp.startsWith(jumpDate)
      ) {
        return false;
      }
      if (!needle) {
        return true;
      }
      return (
        event.description.toLowerCase().includes(needle) ||
        event.event_type.toLowerCase().includes(needle) ||
        event.source.toLowerCase().includes(needle)
      );
    });
  }, [events, jumpDate, query]);

  const byDay = useMemo(() => {
    const map = new Map<string, typeof filtered>();
    for (const event of filtered) {
      const day = event.normalized_timestamp
        ? event.normalized_timestamp.slice(0, 10)
        : "Unknown date";
      const list = map.get(day) ?? [];
      list.push(event);
      map.set(day, list);
    }
    return [...map.entries()];
  }, [filtered]);

  const toggleProvenance = (eventId: string) => {
    setExpanded((current) => ({ ...current, [eventId]: !current[eventId] }));
  };

  return (
    <WorkspacePanelChrome
      description="Deterministic investigation timeline reconstructed from evidence, custody, processing, AI, fusion, and report timestamps."
      exportText={filtered
        .map(
          (event) =>
            `${event.normalized_timestamp ?? "unknown"}\t${event.event_type}\t${event.description}`,
        )
        .join("\n")}
      panelId={`timeline:${caseId}`}
      title="Investigation Timeline"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 flex-1 flex-col gap-2 sm:flex-row">
            <label className="relative min-w-0 flex-1">
              <span className="sr-only">Search events</span>
              <Search
                aria-hidden="true"
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle"
                size={14}
              />
              <Input
                className="pl-8"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search events…"
                value={query}
              />
            </label>
            <Input
              aria-label="Jump to date"
              className="sm:w-44"
              onChange={(event) => setJumpDate(event.target.value)}
              type="date"
              value={jumpDate}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              onClick={() =>
                setZoom((current) =>
                  current === "compact" ? "comfortable" : "compact",
                )
              }
              size="sm"
              variant="secondary"
            >
              Zoom: {zoom}
            </Button>
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

        {!latestQuery.isLoading &&
          (isNotFound || events.length === 0) &&
          !isGenerating && (
            <EmptyState
              description="Reconstruct the timeline to collect chronological events across all case evidence."
              icon={<Clock3 aria-hidden="true" size={19} />}
              title="No timeline events"
            />
          )}

        {conflicts.length > 0 && (
          <div className="space-y-2 rounded-lg border border-warning/50 bg-warning-soft p-3">
            <p className="text-xs font-medium text-warning">
              Timestamp conflicts ({conflicts.length})
            </p>
            {conflicts.map((conflict) => (
              <div
                className="text-xs text-warning/90"
                key={conflict.conflict_id}
              >
                <Badge tone="warning">
                  {conflict.conflict_type.replaceAll("_", " ")}
                </Badge>
                <span className="ml-2">{conflict.explanation}</span>
              </div>
            ))}
          </div>
        )}

        {byDay.length > 0 && !isGenerating && (
          <div className="space-y-4">
            <InteractiveTimelineViz events={filtered} />
            {byDay.map(([day, dayEvents]) => {
              const dayCollapsed = collapsedDays[day] ?? false;
              return (
                <section key={day}>
                  <button
                    className="sticky top-0 z-[1] mb-2 flex w-full items-center justify-between rounded-md border border-border bg-surface/95 px-3 py-2 text-left backdrop-blur"
                    onClick={() =>
                      setCollapsedDays((current) => ({
                        ...current,
                        [day]: !dayCollapsed,
                      }))
                    }
                    type="button"
                  >
                    <span className="text-caption font-semibold text-foreground">
                      {day}
                    </span>
                    <span className="text-micro text-subtle">
                      {dayEvents.length} events ·{" "}
                      {dayCollapsed ? "expand" : "collapse"}
                    </span>
                  </button>
                  {!dayCollapsed && (
                    <div
                      className={
                        zoom === "compact" ? "space-y-2" : "space-y-3"
                      }
                    >
                      {dayEvents.map((event) => {
                        const isOpen = expanded[event.event_id] ?? false;
                        return (
                          <div
                            className="rounded-lg border border-border bg-background/40 p-3"
                            key={event.event_id}
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge
                                tone={
                                  event.normalized_timestamp
                                    ? "primary"
                                    : "neutral"
                                }
                              >
                                {event.event_type.replaceAll("_", " ")}
                              </Badge>
                              <Badge tone={confidenceTone(event.confidence)}>
                                confidence{" "}
                                {(event.confidence * 100).toFixed(0)}%
                              </Badge>
                              <Badge tone="neutral">{event.source}</Badge>
                              <span className="text-[11px] text-muted">
                                {event.normalized_timestamp
                                  ? new Date(
                                      event.normalized_timestamp,
                                    ).toLocaleString()
                                  : "Timestamp unknown"}
                              </span>
                            </div>
                            <p className="mt-2 text-xs text-muted">
                              {event.description}
                            </p>
                            <button
                              className="mt-2 flex items-center gap-1 text-[11px] text-muted hover:text-foreground"
                              onClick={() => toggleProvenance(event.event_id)}
                              type="button"
                            >
                              {isOpen ? (
                                <ChevronDown size={12} />
                              ) : (
                                <ChevronRight size={12} />
                              )}
                              Provenance
                            </button>
                            {isOpen && (
                              <pre className="mt-2 overflow-x-auto rounded bg-background-offset/70 p-2 font-mono text-[10px] text-muted">
                                {JSON.stringify(event.provenance, null, 2)}
                              </pre>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </section>
              );
            })}
          </div>
        )}
      </div>
    </WorkspacePanelChrome>
  );
}
