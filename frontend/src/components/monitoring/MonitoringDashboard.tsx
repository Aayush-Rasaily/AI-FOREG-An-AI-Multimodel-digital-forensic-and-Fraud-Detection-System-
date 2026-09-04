import { RefreshCw } from "lucide-react";

import { PageHeader } from "../layout/PageHeader";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import {
  useMonitoringDashboardQuery,
  useRefreshMonitoringMutation,
} from "../../hooks/useMonitoring";
import { ActivityTimeline } from "./ActivityTimeline";
import { AiMetricsPanel } from "./AiMetricsPanel";
import { ApiMetricsPanel } from "./ApiMetricsPanel";
import { AuditAnalyticsPanel } from "./AuditAnalyticsPanel";
import { ProcessingMetricsPanel } from "./ProcessingMetricsPanel";
import { SystemHealthCard } from "./SystemHealthCard";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

export function MonitoringDashboard() {
  const query = useMonitoringDashboardQuery();
  const refresh = useRefreshMonitoringMutation();
  const dashboard = query.data?.data;

  if (query.isLoading) {
    return <LoadingState label="Loading operational monitoring" />;
  }

  if (query.isError) {
    return (
      <ErrorState
        description="Operational monitoring could not be loaded."
        onRetry={() => void query.refetch()}
        title="Monitoring error"
      />
    );
  }

  if (!dashboard) {
    return (
      <EmptyState
        action={
          <Button onClick={() => void refresh.mutateAsync()}>
            Refresh monitoring
          </Button>
        }
        description="No monitoring snapshot is available yet."
        title="No monitoring data"
      />
    );
  }

  const health = dashboard.system_health;
  const bottlenecks = asRecord(dashboard.bottlenecks);
  const failures = Array.isArray(dashboard.recent_failures)
    ? dashboard.recent_failures
    : [];
  const kpis = asRecord(dashboard.kpis);
  const trends = asRecord(dashboard.trends);
  const cases = asRecord(dashboard.cases);
  const reports = asRecord(dashboard.reports);

  return (
    <div>
      <PageHeader
        actions={
          <Button
            disabled={refresh.isPending}
            onClick={() => void refresh.mutateAsync()}
            size="sm"
            variant="secondary"
          >
            <RefreshCw size={14} /> Refresh
          </Button>
        }
        description="Deterministic operational intelligence derived from persisted platform data."
        eyebrow="Operations"
        title="Monitoring Dashboard"
      />

      <div className="space-y-4">
        <SystemHealthCard
          assessedAt={health.assessed_at}
          reasons={health.reasons}
          status={health.status}
        />

        <div className="grid gap-4 xl:grid-cols-2">
          <ProcessingMetricsPanel data={asRecord(dashboard.processing)} />
          <AiMetricsPanel data={asRecord(dashboard.ai)} />
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <Panel description="Case and evidence inventory." title="Case Summary">
            <dl className="grid grid-cols-2 gap-3 p-4 text-xs">
              <div>
                <dt className="text-slate-500">Cases</dt>
                <dd className="text-slate-200">
                  {String(cases.cases_created ?? 0)}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Evidence</dt>
                <dd className="text-slate-200">
                  {String(cases.evidence_uploaded ?? 0)}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Timelines</dt>
                <dd className="text-slate-200">
                  {String(cases.timelines_created ?? 0)}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Correlations</dt>
                <dd className="text-slate-200">
                  {String(cases.correlation_runs ?? 0)}
                </dd>
              </div>
            </dl>
          </Panel>
          <Panel description="Report generation statistics." title="Report Summary">
            <dl className="grid grid-cols-2 gap-3 p-4 text-xs">
              <div>
                <dt className="text-slate-500">Generated</dt>
                <dd className="text-slate-200">
                  {String(reports.reports_generated ?? 0)}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Avg ms</dt>
                <dd className="text-slate-200">
                  {String(reports.average_generation_ms ?? "n/a")}
                </dd>
              </div>
            </dl>
          </Panel>
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <ApiMetricsPanel data={asRecord(dashboard.api)} />
          <AuditAnalyticsPanel data={asRecord(dashboard.audit_summary)} />
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <ActivityTimeline data={asRecord(dashboard.activity)} />
          <Panel description="Top operational bottlenecks and failures." title="Top Bottlenecks">
            <div className="space-y-3 p-4 text-xs">
              <p className="text-slate-400">
                Inactive investigations:{" "}
                {Array.isArray(bottlenecks.inactive_investigations)
                  ? bottlenecks.inactive_investigations.length
                  : 0}
              </p>
              {failures.length === 0 ? (
                <p className="text-slate-500">No recent processing failures.</p>
              ) : (
                <ul className="space-y-1">
                  {failures.slice(0, 5).map((item) => (
                    <li
                      className="text-slate-300"
                      key={String(item.job_id ?? item.job_type)}
                    >
                      {String(item.job_type)} · {String(item.status)} ·{" "}
                      {String(item.error_code ?? "n/a")}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Panel>
        </div>

        <Panel description="Operational KPI snapshot." title="Trend Metrics">
          <dl className="grid grid-cols-2 gap-3 p-4 text-xs md:grid-cols-3">
            {Object.entries({ ...trends, ...kpis }).map(([key, value]) => (
              <div key={key}>
                <dt className="text-slate-500">{key.replaceAll("_", " ")}</dt>
                <dd className="text-slate-200">{String(value ?? "n/a")}</dd>
              </div>
            ))}
          </dl>
        </Panel>
      </div>
    </div>
  );
}

export { MonitoringDashboard as MonitoringDashboardPage };
