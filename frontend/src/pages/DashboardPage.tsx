import {
  lazy,
  Suspense,
  useMemo,
  type ComponentType,
  type ReactNode,
} from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  FileArchive,
  FileBarChart,
  FolderSearch,
  Gauge,
  GitBranch,
  GitMerge,
  ShieldAlert,
} from "lucide-react";

import { StatCard } from "../components/dashboard/StatCard";
import { SystemStatusCard } from "../components/dashboard/SystemStatusCard";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { LoadingSkeleton } from "../components/ui/Skeleton";
import { NetworkErrorState } from "../components/ui/NetworkErrorState";
import {
  useExecutiveDashboardData,
  type ExecutiveKpi,
} from "../hooks/useExecutiveDashboard";

const DashboardBarChart = lazy(() =>
  import("../components/dashboard/DashboardCharts").then((m) => ({
    default: m.DashboardBarChart,
  })),
);
const DashboardSparkChart = lazy(() =>
  import("../components/dashboard/DashboardCharts").then((m) => ({
    default: m.DashboardSparkChart,
  })),
);
const ActivityFeed = lazy(() =>
  import("../components/dashboard/ActivityFeed").then((m) => ({
    default: m.ActivityFeed,
  })),
);
const RecentCasesWidget = lazy(() =>
  import("../components/dashboard/RecentCasesWidget").then((m) => ({
    default: m.RecentCasesWidget,
  })),
);
const ProcessingQueueWidget = lazy(() =>
  import("../components/dashboard/ProcessingQueueWidget").then((m) => ({
    default: m.ProcessingQueueWidget,
  })),
);
const RiskHeatmap = lazy(() =>
  import("../components/dashboard/RiskHeatmap").then((m) => ({
    default: m.RiskHeatmap,
  })),
);
const InvestigationSummaryCards = lazy(() =>
  import("../components/dashboard/InvestigationSummaryCards").then((m) => ({
    default: m.InvestigationSummaryCards,
  })),
);

const kpiIcons: Record<
  string,
  ComponentType<{ size?: number; strokeWidth?: number }>
> = {
  open: FolderSearch,
  completed: BarChart3,
  evidence: FileArchive,
  jobs: Activity,
  risk: AlertTriangle,
  fusion: GitMerge,
  correlation: GitBranch,
  reports: FileBarChart,
  confidence: Gauge,
  "risk-score": ShieldAlert,
};

function WidgetFallback() {
  return (
    <Card>
      <CardContent className="py-6">
        <LoadingSkeleton rows={4} />
      </CardContent>
    </Card>
  );
}

function Section({
  id,
  title,
  description,
  children,
}: {
  id: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section aria-labelledby={id} className="min-w-0 space-y-3">
      <div>
        <h2 className="text-sm font-semibold text-foreground" id={id}>
          {title}
        </h2>
        <p className="mt-0.5 text-caption text-muted">{description}</p>
      </div>
      {children}
    </section>
  );
}

export function DashboardPage() {
  const data = useExecutiveDashboardData();
  const {
    casesQuery,
    analyticsQuery,
    healthQuery,
    metricsQuery,
    jobsQuery,
    kpis,
    caseStatusChart,
    riskChart,
    evidenceTypeChart,
    fusionVerdictChart,
    correlationTypeChart,
    timelineActivity,
    processingThroughput,
    reportGeneration,
    recentCases,
    activity,
    investigationSummary,
    queue,
    priorityCounts,
  } = data;

  const corePending = casesQuery.isPending || analyticsQuery.isPending;
  const coreError = casesQuery.isError && analyticsQuery.isError;

  const kpiCards = useMemo(
    () =>
      kpis.map((kpi: ExecutiveKpi) => (
        <StatCard
          detail={kpi.detail}
          icon={kpiIcons[kpi.key] ?? Activity}
          key={kpi.key}
          label={kpi.label}
          tone={kpi.tone}
          trend={kpi.trend}
          value={kpi.value}
        />
      )),
    [kpis],
  );

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        description="Situational awareness for investigators, supervisors, and forensic managers — driven by live case, analytics, and platform signals."
        eyebrow="Executive overview"
        title="Investigation dashboard"
        actions={
          <div className="flex flex-wrap gap-2">
            <Button
              onClick={() => {
                void casesQuery.refetch();
                void analyticsQuery.refetch();
                void healthQuery.refetch();
                void metricsQuery.refetch();
                void jobsQuery.refetch();
              }}
              size="sm"
              variant="secondary"
            >
              Refresh
            </Button>
          </div>
        }
      />

      {coreError ? (
        <NetworkErrorState
          onRetry={() => {
            void casesQuery.refetch();
            void analyticsQuery.refetch();
          }}
        />
      ) : null}

      <Section
        description="Enterprise KPIs from case registry and analytics snapshots"
        id="kpi-overview"
        title="Case overview"
      >
        {corePending ? (
          <LoadingSkeleton rows={3} />
        ) : (
          <div
            aria-label="Key performance indicators"
            className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5"
          >
            {kpiCards}
          </div>
        )}
      </Section>

      <Section
        description="Coverage across forensic pipelines"
        id="investigation-summary"
        title="Investigation progress"
      >
        <Suspense fallback={<WidgetFallback />}>
          <InvestigationSummaryCards {...investigationSummary} />
        </Suspense>
      </Section>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Section
          description="Priority mix across the case registry"
          id="risk-overview"
          title="Risk overview"
        >
          <Suspense fallback={<WidgetFallback />}>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <DashboardBarChart
                description="Case priority distribution"
                slices={riskChart}
                title="Risk distribution"
              />
              <RiskHeatmap counts={priorityCounts} />
            </div>
          </Suspense>
        </Section>
        <Section
          description="API health and worker connectivity"
          id="system-status"
          title="Platform health"
        >
          <SystemStatusCard
            activeAnalyses={queue.activeAnalyses}
            error={healthQuery.isError}
            health={healthQuery.data?.data}
            jobsConnected={Boolean(jobsQuery.data)}
            loading={healthQuery.isPending}
          />
        </Section>
      </div>

      <Section
        description="Evidence mix, case status, fusion and correlation signals"
        id="evidence-summary"
        title="Evidence & intelligence charts"
      >
        <Suspense fallback={<WidgetFallback />}>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            <DashboardBarChart
              description="Breakdown from analytics when available"
              emptyLabel="No evidence type breakdown yet"
              slices={evidenceTypeChart}
              title="Evidence by type"
            />
            <DashboardBarChart
              description="Open through archived"
              slices={caseStatusChart}
              title="Case status"
            />
            <DashboardBarChart
              description="Cross-modal fusion outcomes"
              emptyLabel="No fusion runs recorded"
              slices={fusionVerdictChart}
              title="Fusion verdicts"
            />
            <DashboardBarChart
              description="Relationship matches"
              emptyLabel="No correlation matches yet"
              slices={correlationTypeChart}
              title="Correlation types"
            />
            <DashboardSparkChart
              description="Case update cadence / analytics trend"
              emptyLabel="No timeline activity yet"
              points={timelineActivity}
              title="Timeline activity"
            />
            <DashboardSparkChart
              description="Queue throughput or analytics series"
              emptyLabel="No processing series yet"
              points={processingThroughput}
              title="Processing throughput"
            />
            <DashboardSparkChart
              description="Report generation trend"
              emptyLabel="No reports generated yet"
              points={reportGeneration}
              title="Report generation"
            />
          </div>
        </Suspense>
      </Section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Section
          description="Queue depth and job outcomes"
          id="processing-queue"
          title="Processing queue"
        >
          <Suspense fallback={<WidgetFallback />}>
            <ProcessingQueueWidget {...queue} />
          </Suspense>
        </Section>
        <Section
          description="Newest signals first"
          id="recent-activity"
          title="Recent activity"
        >
          <Suspense fallback={<WidgetFallback />}>
            <ActivityFeed items={activity} />
          </Suspense>
        </Section>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        <Section
          description="Quick open into investigation workspaces"
          id="recent-cases"
          title="Recent cases"
        >
          <Suspense fallback={<WidgetFallback />}>
            <RecentCasesWidget cases={recentCases} />
          </Suspense>
        </Section>
        <Section
          description="Fusion, correlation, timeline, and report readiness"
          id="report-status"
          title="Fusion · Correlation · Timeline · Reports"
        >
          <Card>
            <CardHeader>
              <CardTitle>Intelligence status</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3 sm:grid-cols-2">
              {[
                {
                  label: "Fusion",
                  value: investigationSummary.fusionCompleted,
                },
                {
                  label: "Correlation",
                  value: investigationSummary.correlationCompleted,
                },
                {
                  label: "Timelines",
                  value: investigationSummary.timelineGenerated,
                },
                {
                  label: "Reports",
                  value: investigationSummary.reportsAvailable,
                },
              ].map((row) => (
                <div
                  className="rounded-lg border border-border bg-background/40 p-3"
                  key={row.label}
                >
                  <p className="text-micro uppercase tracking-wider text-subtle">
                    {row.label}
                  </p>
                  <p className="mt-1 text-xl font-semibold text-foreground">
                    {row.value}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        </Section>
      </div>
    </div>
  );
}
