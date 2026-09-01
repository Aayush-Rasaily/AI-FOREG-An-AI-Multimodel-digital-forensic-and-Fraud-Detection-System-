import { Clock3 } from "lucide-react";

import {
  useAnalyzeCaseIntelligenceMutation,
  useCaseIntelligenceLatestQuery,
  useCaseTimelineQuery,
} from "../../hooks/useCaseIntelligence";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface CaseTimelinePanelProps {
  caseId: string;
}

export function CaseTimelinePanel({ caseId }: CaseTimelinePanelProps) {
  const latestQuery = useCaseIntelligenceLatestQuery(caseId);
  const timelineQuery = useCaseTimelineQuery(
    caseId,
    latestQuery.isSuccess,
  );
  const analyzeMutation = useAnalyzeCaseIntelligenceMutation();

  const isNotFound =
    latestQuery.error instanceof ApiClientError && latestQuery.error.status === 404;
  const events = timelineQuery.data?.data ?? latestQuery.data?.data.timeline ?? [];

  return (
    <Panel
      description="Deterministic case timeline built from known evidence, custody, and fusion timestamps."
      title="Investigation Timeline"
    >
      <div className="space-y-4 p-4">
        <div className="flex justify-end">
          <Button
            disabled={analyzeMutation.isPending}
            onClick={() => analyzeMutation.mutate({ caseId })}
            size="sm"
            variant="secondary"
          >
            {analyzeMutation.isPending ? "Queuing…" : "Refresh Timeline"}
          </Button>
        </div>

        {(latestQuery.isLoading || timelineQuery.isLoading) && (
          <LoadingState label="Loading timeline…" />
        )}

        {!latestQuery.isLoading && latestQuery.isError && !isNotFound && (
          <ErrorState
            description="Unable to load case timeline."
            title="Timeline unavailable"
          />
        )}

        {!latestQuery.isLoading && (isNotFound || events.length === 0) && (
          <EmptyState
            description="Run case synthesis to build a timeline from known timestamps."
            icon={<Clock3 aria-hidden="true" size={19} />}
            title="No timeline events"
          />
        )}

        {events.length > 0 && (
          <div className="space-y-3">
            {events.map((event) => (
              <div
                className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
                key={event.event_id}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={event.timestamp_known ? "cyan" : "neutral"}>
                    {event.event_type.replaceAll("_", " ")}
                  </Badge>
                  <span className="text-[11px] text-slate-500">
                    {event.timestamp_known && event.timestamp
                      ? new Date(event.timestamp).toLocaleString()
                      : "Timestamp unknown"}
                  </span>
                </div>
                <p className="mt-2 text-xs text-slate-300">{event.description}</p>
                <p className="mt-1 font-mono text-[10px] text-slate-600">
                  {event.source_reference}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </Panel>
  );
}
