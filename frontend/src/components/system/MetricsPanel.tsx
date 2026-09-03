import { useSystemMetricsQuery } from "../../hooks/useSystem";
import { Badge } from "../ui/Badge";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

const METRIC_LABELS: Record<string, string> = {
  evidence_count: "Evidence",
  case_count: "Cases",
  report_count: "Reports",
  timeline_count: "Timelines",
  fusion_run_count: "Fusion runs",
  entity_graph_count: "Entity graphs",
  correlation_count: "Correlations",
  ai_analysis_count: "AI analyses",
  processing_job_count: "Processing jobs",
};

export function MetricsPanel() {
  const query = useSystemMetricsQuery();
  const data = query.data?.data;

  return (
    <Panel
      description="Deterministic operational counters."
      title="Metrics"
    >
      <div className="p-4">
        {query.isLoading && <LoadingState label="Loading metrics…" />}
        {query.isError && (
          <ErrorState
            description="Metrics unavailable."
            onRetry={() => void query.refetch()}
            title="Metrics failed"
          />
        )}
        {data && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {Object.entries(METRIC_LABELS).map(([key, label]) => (
                <div
                  className="rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2"
                  key={key}
                >
                  <p className="text-[10px] text-slate-500">{label}</p>
                  <p className="text-sm font-medium text-slate-200">
                    {String(data[key as keyof typeof data] ?? 0)}
                  </p>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Badge tone="neutral">
                Failure rate: {(data.failure_rate * 100).toFixed(1)}%
              </Badge>
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
