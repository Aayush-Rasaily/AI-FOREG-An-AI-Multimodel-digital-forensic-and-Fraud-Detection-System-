import { Check, X } from "lucide-react";

import { useSystemJobsQuery } from "../../hooks/useSystem";
import { Badge } from "../ui/Badge";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function JobsPanel() {
  const query = useSystemJobsQuery();
  const data = query.data?.data;

  return (
    <Panel
      description="Background job status across pipelines."
      title="Jobs"
    >
      <div className="p-4">
        {query.isLoading && <LoadingState label="Loading jobs…" />}
        {query.isError && (
          <ErrorState
            description="Job summary unavailable."
            onRetry={() => void query.refetch()}
            title="Jobs failed"
          />
        )}
        {data && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge tone="primary">
                Queue: {data.queue_length}
              </Badge>
              <Badge tone="warning">
                Active: {data.active_analyses}
              </Badge>
              <Badge tone="success">
                Completed: {data.totals.completed}
              </Badge>
              <Badge tone="error">
                Failed: {data.totals.failed}
              </Badge>
            </div>
            <div className="space-y-2">
              {data.category_list.map((cat) => {
                const counts = data.categories[cat];
                if (!counts) return null;
                return (
                  <div
                    className="rounded border border-border px-3 py-2 text-caption"
                    key={cat}
                  >
                    <span className="font-medium text-foreground">
                      {cat.replaceAll("_", " ")}
                    </span>
                    <span className="ml-2 inline-flex items-center gap-2 text-muted">
                      <span>Q: {counts.queued}</span>
                      <span>R: {counts.running}</span>
                      <span className="inline-flex items-center gap-1 text-success">
                        <Check aria-hidden="true" size={11} />
                        {counts.completed}
                      </span>
                      <span className="inline-flex items-center gap-1 text-danger">
                        <X aria-hidden="true" size={11} />
                        {counts.failed}
                      </span>
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
