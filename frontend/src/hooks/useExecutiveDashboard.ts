import { useMemo } from "react";

import { useAnalyticsQuery } from "./useAnalytics";
import { useCasesQuery } from "./useCases";
import { useHealthQuery } from "./useHealth";
import { useSystemJobsQuery, useSystemMetricsQuery } from "./useSystem";
import type { CaseRecord, CasePriority, CaseStatus } from "../types/case";
import type { AnalyticsMetric } from "../types/analytics";

export interface ExecutiveKpi {
  key: string;
  label: string;
  value: string;
  detail: string;
  trend?: string;
  tone?: "up" | "down" | "flat";
}

export interface ChartSlice {
  label: string;
  value: number;
  tone?: "primary" | "success" | "warning" | "danger" | "neutral" | "info";
}

export interface ActivityItem {
  id: string;
  title: string;
  detail: string;
  at: string;
  kind:
    | "case"
    | "evidence"
    | "analysis"
    | "fusion"
    | "report"
    | "timeline"
    | "system";
}

export interface RecentCaseRow {
  id: string;
  title: string;
  caseNumber: string;
  status: CaseStatus;
  priority: CasePriority;
  updatedAt: string;
  /** Per-case evidence count is not on the list API; null until a detail view loads it. */
  evidenceCount: number | null;
}

function metricMap(metrics: AnalyticsMetric[] | undefined) {
  const map = new Map<string, number>();
  for (const metric of metrics ?? []) {
    map.set(metric.key, metric.value);
    map.set(metric.label.toLowerCase().replaceAll(" ", "_"), metric.value);
  }
  return map;
}

function sectionNumber(section: Record<string, unknown> | undefined, key: string) {
  const value = section?.[key];
  return typeof value === "number" ? value : 0;
}

function countByStatus(cases: CaseRecord[]) {
  const counts: Record<string, number> = {};
  for (const item of cases) {
    counts[item.status] = (counts[item.status] ?? 0) + 1;
  }
  return counts;
}

function countByPriority(cases: CaseRecord[]) {
  const counts: Record<CasePriority, number> = {
    LOW: 0,
    MEDIUM: 0,
    HIGH: 0,
    CRITICAL: 0,
  };
  for (const item of cases) {
    counts[item.priority] += 1;
  }
  return counts;
}

function formatTrend(current: number, previous?: number): {
  trend: string;
  tone: "up" | "down" | "flat";
} {
  if (previous == null || previous === current) {
    return { trend: "Stable vs last snapshot", tone: "flat" };
  }
  const delta = current - previous;
  const pct = previous === 0 ? 100 : Math.round((delta / previous) * 100);
  if (delta > 0) {
    return { trend: `+${pct}% vs prior`, tone: "up" };
  }
  return { trend: `${pct}% vs prior`, tone: "down" };
}

export function useExecutiveDashboardData() {
  const casesQuery = useCasesQuery();
  const analyticsQuery = useAnalyticsQuery();
  const healthQuery = useHealthQuery();
  const metricsQuery = useSystemMetricsQuery();
  const jobsQuery = useSystemJobsQuery();

  const cases = casesQuery.data?.data.items ?? [];
  const caseTotal = casesQuery.data?.data.total ?? cases.length;
  const run = analyticsQuery.data?.data;
  const metrics = metricMap(run?.metrics);
  const sections = (run?.sections ?? {}) as Record<
    string,
    Record<string, unknown>
  >;
  const systemMetrics = metricsQuery.data?.data;
  const jobs = jobsQuery.data?.data;

  const statusCounts = useMemo(() => countByStatus(cases), [cases]);
  const priorityCounts = useMemo(() => countByPriority(cases), [cases]);

  const openCases =
    (statusCounts.OPEN ?? 0) +
    (statusCounts.IN_PROGRESS ?? 0) +
    (statusCounts.ON_HOLD ?? 0);
  const completedCases =
    (statusCounts.COMPLETED ?? 0) + (statusCounts.ARCHIVED ?? 0);

  const evidenceItems =
    systemMetrics?.evidence_count ??
    metrics.get("evidence_count") ??
    sectionNumber(sections.evidence, "processed") ??
    0;

  const processingJobs =
    jobs?.totals
      ? jobs.totals.queued + jobs.totals.running
      : (systemMetrics?.processing_job_count ?? 0);

  const highRiskFindings =
    metrics.get("high_risk_findings") ??
    sectionNumber(sections.integrity, "alerts") ??
    priorityCounts.HIGH + priorityCounts.CRITICAL;

  const fusionRuns =
    systemMetrics?.fusion_run_count ??
    metrics.get("fusion_runs") ??
    sectionNumber(sections.ai, "fusion_runs");

  const correlationMatches =
    systemMetrics?.correlation_count ??
    metrics.get("correlation_matches") ??
    sectionNumber(sections.ai, "correlations");

  const generatedReports =
    systemMetrics?.report_count ??
    metrics.get("reports_generated") ??
    sectionNumber(sections.cases, "reports_generated");

  const avgConfidence =
    metrics.get("average_confidence") ??
    metrics.get("avg_confidence") ??
    (typeof sections.ai?.average_confidence === "number"
      ? (sections.ai.average_confidence as number)
      : null);

  const avgRisk =
    metrics.get("average_risk_score") ??
    metrics.get("avg_risk") ??
    (priorityCounts.CRITICAL * 0.95 +
      priorityCounts.HIGH * 0.75 +
      priorityCounts.MEDIUM * 0.45 +
      priorityCounts.LOW * 0.15) /
      Math.max(cases.length, 1);

  const casesTrend = run?.trends?.cases_opened;
  const priorCases =
    casesTrend && casesTrend.length > 1
      ? casesTrend[casesTrend.length - 2]?.value
      : undefined;

  const kpis: ExecutiveKpi[] = useMemo(() => {
    const openTrend = formatTrend(openCases, priorCases);
    return [
      {
        key: "open",
        label: "Open cases",
        value: String(openCases || caseTotal),
        detail: "Active and in-progress investigations",
        ...openTrend,
      },
      {
        key: "completed",
        label: "Completed cases",
        value: String(completedCases),
        detail: "Completed or archived",
        trend: "From case registry",
        tone: "flat" as const,
      },
      {
        key: "evidence",
        label: "Evidence items",
        value: String(evidenceItems),
        detail: "Registered immutable artifacts",
        trend: "Platform metrics",
        tone: "flat" as const,
      },
      {
        key: "jobs",
        label: "Processing jobs",
        value: String(processingJobs),
        detail: "Queued + running workers",
        trend: jobs ? "Live queue" : "Awaiting jobs API",
        tone: "flat" as const,
      },
      {
        key: "risk",
        label: "High-risk findings",
        value: String(highRiskFindings),
        detail: "Alerts and elevated priorities",
        trend: "Integrity / priority signal",
        tone: highRiskFindings > 0 ? ("up" as const) : ("flat" as const),
      },
      {
        key: "fusion",
        label: "Fusion runs",
        value: String(fusionRuns),
        detail: "Cross-modal fusion executions",
        trend: "Persisted fusion count",
        tone: "flat" as const,
      },
      {
        key: "correlation",
        label: "Correlation matches",
        value: String(correlationMatches),
        detail: "Linked evidence relationships",
        trend: "Correlation engine",
        tone: "flat" as const,
      },
      {
        key: "reports",
        label: "Generated reports",
        value: String(generatedReports),
        detail: "Forensic / case reports",
        trend: "Report registry",
        tone: "flat" as const,
      },
      {
        key: "confidence",
        label: "Average confidence",
        value:
          avgConfidence == null
            ? "—"
            : avgConfidence <= 1
              ? `${Math.round(avgConfidence * 100)}%`
              : avgConfidence.toFixed(1),
        detail: "From analytics when available",
        trend: "Deterministic snapshot",
        tone: "flat" as const,
      },
      {
        key: "risk-score",
        label: "Average risk score",
        value: `${Math.round(avgRisk * 100)}%`,
        detail: "Derived from case priority mix",
        trend: "Priority-weighted",
        tone: avgRisk >= 0.6 ? ("up" as const) : ("flat" as const),
      },
    ];
  }, [
    avgConfidence,
    avgRisk,
    caseTotal,
    completedCases,
    correlationMatches,
    evidenceItems,
    fusionRuns,
    generatedReports,
    highRiskFindings,
    jobs,
    openCases,
    priorCases,
    processingJobs,
  ]);

  const caseStatusChart: ChartSlice[] = useMemo(
    () =>
      (["OPEN", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "ARCHIVED"] as const)
        .map((status) => ({
          label: status.replaceAll("_", " "),
          value: statusCounts[status] ?? 0,
          tone:
            status === "COMPLETED"
              ? ("success" as const)
              : status === "ON_HOLD"
                ? ("warning" as const)
                : ("primary" as const),
        }))
        .filter((slice) => slice.value > 0 || cases.length === 0),
    [cases.length, statusCounts],
  );

  const riskChart: ChartSlice[] = useMemo(
    () => [
      { label: "Low", value: priorityCounts.LOW, tone: "success" as const },
      { label: "Medium", value: priorityCounts.MEDIUM, tone: "info" as const },
      { label: "High", value: priorityCounts.HIGH, tone: "warning" as const },
      {
        label: "Critical",
        value: priorityCounts.CRITICAL,
        tone: "danger" as const,
      },
    ],
    [priorityCounts],
  );

  const evidenceTypeChart: ChartSlice[] = useMemo(() => {
    const breakdown = sections.ai?.breakdown;
    if (breakdown && typeof breakdown === "object") {
      return Object.entries(breakdown as Record<string, number>).map(
        ([label, value]) => ({
          label,
          value: Number(value) || 0,
          tone: "primary" as const,
        }),
      );
    }
    return [
      { label: "Image", value: sectionNumber(sections.ai, "image") || 0 },
      { label: "Document", value: sectionNumber(sections.ai, "document") || 0 },
      { label: "Video", value: sectionNumber(sections.ai, "video") || 0 },
      { label: "Audio", value: sectionNumber(sections.ai, "audio") || 0 },
      {
        label: "Other",
        value: Math.max(
          0,
          (sectionNumber(sections.ai, "analyses_completed") || evidenceItems) -
            sectionNumber(sections.ai, "image") -
            sectionNumber(sections.ai, "document") -
            sectionNumber(sections.ai, "video") -
            sectionNumber(sections.ai, "audio"),
        ),
      },
    ].filter((slice) => slice.value > 0);
  }, [evidenceItems, sections.ai]);

  const fusionVerdictChart: ChartSlice[] = useMemo(() => {
    const verdicts = sections.ai?.fusion_verdicts;
    if (verdicts && typeof verdicts === "object") {
      return Object.entries(verdicts as Record<string, number>).map(
        ([label, value]) => ({
          label,
          value: Number(value) || 0,
          tone: "primary" as const,
        }),
      );
    }
    return fusionRuns > 0
      ? [{ label: "Recorded runs", value: fusionRuns, tone: "primary" as const }]
      : [];
  }, [fusionRuns, sections.ai]);

  const correlationTypeChart: ChartSlice[] = useMemo(() => {
    const types = sections.ai?.correlation_types;
    if (types && typeof types === "object") {
      return Object.entries(types as Record<string, number>).map(
        ([label, value]) => ({
          label,
          value: Number(value) || 0,
        }),
      );
    }
    return correlationMatches > 0
      ? [{ label: "Matches", value: correlationMatches }]
      : [];
  }, [correlationMatches, sections.ai]);

  const timelineActivity = useMemo(() => {
    const series = run?.trends?.timeline_events ?? run?.trends?.cases_opened;
    if (series?.length) {
      return series.map((point) => ({
        label: point.label,
        value: point.value,
      }));
    }
    return cases
      .slice()
      .sort((a, b) => a.updated_at.localeCompare(b.updated_at))
      .slice(-8)
      .map((item, index) => ({
        label: item.case_number,
        value: index + 1,
      }));
  }, [cases, run?.trends]);

  const processingThroughput = useMemo(() => {
    const series = run?.trends?.processing_throughput;
    if (series?.length) {
      return series.map((point) => ({
        label: point.label,
        value: point.value,
      }));
    }
    const totals = jobs?.totals;
    return [
      { label: "Queued", value: totals?.queued ?? 0 },
      { label: "Running", value: totals?.running ?? 0 },
      { label: "Completed", value: totals?.completed ?? 0 },
      { label: "Failed", value: totals?.failed ?? 0 },
    ];
  }, [jobs?.totals, run?.trends]);

  const reportGeneration = useMemo(() => {
    const series = run?.trends?.reports_generated;
    if (series?.length) {
      return series.map((point) => ({
        label: point.label,
        value: point.value,
      }));
    }
    return generatedReports > 0
      ? [{ label: "Generated", value: generatedReports }]
      : [];
  }, [generatedReports, run?.trends]);

  const recentCases: RecentCaseRow[] = useMemo(
    () =>
      [...cases]
        .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
        .slice(0, 6)
        .map((item) => ({
          id: item.id,
          title: item.title,
          caseNumber: item.case_number,
          status: item.status,
          priority: item.priority,
          updatedAt: item.updated_at,
          evidenceCount: null,
        })),
    [cases],
  );

  const activity: ActivityItem[] = useMemo(() => {
    const items: ActivityItem[] = [];
    for (const item of recentCases) {
      items.push({
        id: `case-${item.id}`,
        title: `Case updated · ${item.caseNumber}`,
        detail: `${item.title} · ${item.status.replaceAll("_", " ")}`,
        at: item.updatedAt,
        kind: "case",
      });
    }
    if (run?.completed_at) {
      items.push({
        id: "analytics",
        title: "Analytics snapshot refreshed",
        detail: `${run.metric_count} metrics · ${run.status}`,
        at: run.completed_at,
        kind: "system",
      });
    }
    if (systemMetrics) {
      items.push({
        id: "metrics",
        title: "Platform metrics available",
        detail: `${systemMetrics.case_count} cases · ${systemMetrics.evidence_count} evidence`,
        at: new Date().toISOString(),
        kind: "evidence",
      });
    }
    if (fusionRuns > 0) {
      items.push({
        id: "fusion",
        title: "Fusion activity recorded",
        detail: `${fusionRuns} fusion run(s) in platform metrics`,
        at: run?.completed_at ?? new Date().toISOString(),
        kind: "fusion",
      });
    }
    if (generatedReports > 0) {
      items.push({
        id: "reports",
        title: "Reports generated",
        detail: `${generatedReports} report(s) available`,
        at: run?.completed_at ?? new Date().toISOString(),
        kind: "report",
      });
    }
    if ((systemMetrics?.timeline_count ?? 0) > 0) {
      items.push({
        id: "timeline",
        title: "Timeline reconstructions present",
        detail: `${systemMetrics?.timeline_count} timeline(s)`,
        at: run?.completed_at ?? new Date().toISOString(),
        kind: "timeline",
      });
    }
    return items
      .sort((a, b) => b.at.localeCompare(a.at))
      .slice(0, 12);
  }, [
    fusionRuns,
    generatedReports,
    recentCases,
    run?.completed_at,
    run?.metric_count,
    run?.status,
    systemMetrics,
  ]);

  const investigationSummary = {
    evidenceAnalyzed:
      sectionNumber(sections.evidence, "processed") || evidenceItems,
    modalitiesAvailable: evidenceTypeChart.length,
    fusionCompleted: fusionRuns,
    correlationCompleted: correlationMatches,
    timelineGenerated: systemMetrics?.timeline_count ?? 0,
    reportsAvailable: generatedReports,
  };

  const queue = {
    running: jobs?.totals.running ?? 0,
    queued: jobs?.totals.queued ?? jobs?.queue_length ?? 0,
    completed: jobs?.totals.completed ?? 0,
    failed: jobs?.totals.failed ?? 0,
    activeAnalyses: jobs?.active_analyses ?? 0,
  };

  return {
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
    caseTotal,
    run,
    systemMetrics,
  };
}
