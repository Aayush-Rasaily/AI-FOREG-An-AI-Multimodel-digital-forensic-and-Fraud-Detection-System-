import { useState } from "react";
import { BarChart3, RefreshCw } from "lucide-react";

import {
  useAnalyticsExportMutation,
  useAnalyticsQuery,
  useRefreshAnalyticsMutation,
} from "../../hooks/useAnalytics";
import { ExportPanel } from "./ExportPanel";
import { KpiCards } from "./KpiCards";
import { SectionMetrics } from "./SectionMetrics";
import { TrendCharts } from "./TrendCharts";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { PageHeader } from "../layout/PageHeader";

export function AnalyticsDashboard() {
  const query = useAnalyticsQuery();
  const refreshMutation = useRefreshAnalyticsMutation();
  const exportMutation = useAnalyticsExportMutation();
  const [lastExport, setLastExport] = useState<string | null>(null);

  const run = query.data?.data;
  const overview = (run?.sections?.overview ?? {}) as {
    kpis?: Array<{ key: string; label: string; value: number; unit: string }>;
  };
  const cases = (run?.sections?.cases ?? {}) as Record<string, unknown>;
  const evidence = (run?.sections?.evidence ?? {}) as Record<string, unknown>;
  const ai = (run?.sections?.ai ?? {}) as Record<string, unknown>;
  const workflow = (run?.sections?.workflow ?? {}) as Record<string, unknown>;
  const integrity = (run?.sections?.integrity ?? {}) as Record<string, unknown>;

  return (
    <div className="space-y-4">
      <PageHeader
        description="Deterministic operational insights from persisted investigation data — no forecasting or AI re-runs."
        eyebrow="Operations"
        title="Investigation Analytics"
      />

      <Panel
        description="Refresh to persist a new analytics snapshot from current platform tables."
        title="Analytics Dashboard"
      >
        <div className="space-y-4 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              {run ? (
                <>
                  <Badge tone="cyan">{run.status}</Badge>
                  <Badge tone="neutral">{run.metric_count} metrics</Badge>
                  <Badge tone={run.persisted ? "green" : "amber"}>
                    {run.persisted ? "persisted" : "live"}
                  </Badge>
                </>
              ) : (
                <Badge tone="neutral">No snapshot</Badge>
              )}
            </div>
            <Button
              disabled={refreshMutation.isPending}
              onClick={() => refreshMutation.mutate()}
              size="sm"
            >
              <RefreshCw size={14} /> Refresh analytics
            </Button>
          </div>

          {query.isLoading ? (
            <LoadingState label="Loading analytics" />
          ) : null}
          {query.isError ? (
            <ErrorState
              description="Unable to load analytics."
              title="Analytics unavailable"
            />
          ) : null}
          {refreshMutation.isError ? (
            <ErrorState
              description="Analytics refresh failed."
              title="Refresh error"
            />
          ) : null}

          {run?.provenance ? (
            <div className="text-[11px] text-slate-600">
              Provenance · engine {run.engine_version} · policy{" "}
              {run.policy_version} · forecasting off
            </div>
          ) : null}
        </div>
      </Panel>

      <KpiCards items={overview.kpis ?? []} />
      <TrendCharts trends={run?.trends ?? {}} />

      <div className="grid gap-4 xl:grid-cols-2">
        <SectionMetrics
          data={cases}
          description="Case lifecycle totals."
          title="Case Metrics"
        />
        <SectionMetrics
          data={ai}
          description="AI and fusion utilization from stored runs."
          title="AI Usage Metrics"
        />
        <SectionMetrics
          data={workflow}
          description="Workflow, review, and queue utilization."
          title="Workflow Metrics"
        />
        <SectionMetrics
          data={evidence}
          description="Evidence volume, timeline, correlations, storage."
          title="Evidence Metrics"
        />
        <SectionMetrics
          data={integrity}
          description="Integrity monitoring alert and run counts."
          title="Integrity Metrics"
        />
        <ExportPanel
          exporting={exportMutation.isPending}
          lastExport={lastExport}
          onExport={() => {
            exportMutation.mutate(undefined, {
              onSuccess: (response) => {
                const payload = JSON.stringify(response.data, null, 2);
                const blob = new Blob([payload], {
                  type: "application/json",
                });
                const url = URL.createObjectURL(blob);
                const anchor = document.createElement("a");
                anchor.href = url;
                anchor.download = "investigation-analytics.json";
                anchor.click();
                URL.revokeObjectURL(url);
                setLastExport(new Date().toLocaleString());
              },
            });
          }}
        />
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-600">
        <BarChart3 size={14} /> Operational metrics only — no predictive models.
      </div>
    </div>
  );
}
