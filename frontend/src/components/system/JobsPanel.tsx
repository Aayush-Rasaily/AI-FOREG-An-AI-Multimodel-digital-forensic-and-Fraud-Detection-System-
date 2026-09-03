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
              <Badge tone="cyan">
                Queue: {data.queue_length}
              </Badge>
              <Badge tone="amber">
                Active: {data.active_analyses}
              </Badge>
              <Badge tone="green">
                Completed: {data.totals.completed}
              </Badge>
              <Badge tone="red">
                Failed: {data.totals.failed}
              </Badge>
            </div>
            <div className="space-y-2">
              {data.category_list.map((cat) => {
                const counts = data.categories[cat];
                if (!counts) return null;
                return (
                  <div
                    className="rounded border border-slate-800 px-3 py-2 text-xs"
                    key={cat}
                  >
                    <span className="font-medium text-slate-200">
                      {cat.replaceAll("_", " ")}
                    </span>
                    <span className="ml-2 text-slate-500">
                      Q:{counts.queued} R:{counts.running} ✓:
                      {counts.completed} ✗:{counts.failed}
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
