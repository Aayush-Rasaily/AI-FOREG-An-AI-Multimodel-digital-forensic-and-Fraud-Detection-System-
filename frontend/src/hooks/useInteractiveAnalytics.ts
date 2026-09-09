import { useMemo, useState } from "react";

import type { InsightItem } from "../components/viz/AnalyticsInsightWidgets";
import type { HeatCell } from "../components/viz/HeatmapGrid";
import {
  DEFAULT_ANALYTICS_FILTERS,
  type AnalyticsFilterState,
  type GraphEdge,
  type GraphNode,
  type VizSlice,
} from "../components/viz/types";
import type { CasePriority, CaseRecord } from "../types/case";
import { useAnalyticsQuery } from "./useAnalytics";
import { useCasesQuery } from "./useCases";
import { useSystemJobsQuery, useSystemMetricsQuery } from "./useSystem";

function sectionNumber(section: Record<string, unknown> | undefined, key: string) {
  const value = section?.[key];
  return typeof value === "number" ? value : 0;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function withinDate(iso: string, from: string, to: string) {
  const day = iso.slice(0, 10);
  if (from && day < from) return false;
  if (to && day > to) return false;
  return true;
}

export function useInteractiveAnalytics() {
  const analyticsQuery = useAnalyticsQuery();
  const casesQuery = useCasesQuery();
  const metricsQuery = useSystemMetricsQuery();
  const jobsQuery = useSystemJobsQuery();
  const [filters, setFilters] = useState<AnalyticsFilterState>(
    DEFAULT_ANALYTICS_FILTERS,
  );

  const run = analyticsQuery.data?.data;
  const sections = asRecord(run?.sections);
  const casesSection = asRecord(sections.cases);
  const aiSection = asRecord(sections.ai);
  const integritySection = asRecord(sections.integrity);
  const cases = casesQuery.data?.data.items ?? [];
  const metrics = metricsQuery.data?.data;
  const jobs = jobsQuery.data?.data;

  const filteredCases = useMemo(() => {
    return cases.filter((item) => {
      if (filters.caseId !== "all" && item.id !== filters.caseId) return false;
      if (filters.status !== "all" && item.status !== filters.status) return false;
      if (filters.risk !== "all" && item.priority !== filters.risk) return false;
      if (!withinDate(item.updated_at, filters.dateFrom, filters.dateTo)) {
        return false;
      }
      return true;
    });
  }, [cases, filters]);

  const evidenceBreakdown = useMemo(() => {
    const breakdown = asRecord(aiSection.breakdown);
    const entries = Object.entries(breakdown)
      .filter(([, v]) => typeof v === "number")
      .map(([label, value]) => ({ label, value: value as number }));
    if (entries.length) return entries;
    return ["image", "document", "video", "audio"]
      .map((label) => ({
        label,
        value: sectionNumber(aiSection, label),
      }))
      .filter((e) => e.value > 0);
  }, [aiSection]);

  const evidenceTypes = evidenceBreakdown.map((e) => e.label);
  const modalities = evidenceTypes.length
    ? evidenceTypes
    : ["image", "document", "video", "audio"];

  const correlationEntries = useMemo(() => {
    const types = asRecord(aiSection.correlation_types);
    const entries = Object.entries(types)
      .filter(([, v]) => typeof v === "number")
      .map(([label, value]) => ({ label, value: value as number }));
    if (entries.length) return entries;
    const matches =
      metrics?.correlation_count ?? sectionNumber(aiSection, "correlations");
    return matches > 0 ? [{ label: "Matches", value: matches }] : [];
  }, [aiSection, metrics?.correlation_count]);

  const applyEvidenceFilter = (slices: VizSlice[]) => {
    if (filters.evidenceType === "all") return slices;
    return slices.filter(
      (s) => s.label.toLowerCase() === filters.evidenceType.toLowerCase(),
    );
  };

  const applyModalityFilter = (slices: VizSlice[]) => {
    if (filters.aiModality === "all") return slices;
    return slices.filter(
      (s) => s.label.toLowerCase() === filters.aiModality.toLowerCase(),
    );
  };

  const applyCorrelationFilter = (slices: VizSlice[]) => {
    if (filters.correlationType === "all") return slices;
    return slices.filter(
      (s) =>
        s.label.toLowerCase() === filters.correlationType.toLowerCase(),
    );
  };

  const applySliceHighlight = (slices: VizSlice[]) => {
    if (!filters.selectedSliceId) return slices;
    const hit = slices.find((s) => s.id === filters.selectedSliceId);
    return hit ? [hit] : slices;
  };

  const evidenceTypeChart: VizSlice[] = useMemo(() => {
    const slices = evidenceBreakdown.map((e) => ({
      id: `evidence-${e.label}`,
      label: e.label,
      value: e.value,
      tone: "primary" as const,
    }));
    return applySliceHighlight(
      applyModalityFilter(applyEvidenceFilter(slices)),
    );
  }, [
    evidenceBreakdown,
    filters.aiModality,
    filters.evidenceType,
    filters.selectedSliceId,
  ]);

  const investigationProgressChart: VizSlice[] = useMemo(() => {
    const statusOrder = [
      "OPEN",
      "IN_PROGRESS",
      "ON_HOLD",
      "COMPLETED",
      "ARCHIVED",
    ] as const;
    const counts: Record<string, number> = {};
    for (const item of filteredCases) {
      counts[item.status] = (counts[item.status] ?? 0) + 1;
    }
    const slices = statusOrder.map((status) => ({
      id: `status-${status}`,
      label: status.replaceAll("_", " "),
      value: counts[status] ?? 0,
      tone:
        status === "COMPLETED"
          ? ("success" as const)
          : status === "ON_HOLD"
            ? ("warning" as const)
            : ("primary" as const),
    }));
    return applySliceHighlight(slices.filter((s) => s.value > 0 || filteredCases.length === 0));
  }, [filteredCases, filters.selectedSliceId]);

  const processingJobsChart: VizSlice[] = useMemo(() => {
    const totals = jobs?.totals;
    const slices = [
      { id: "jobs-queued", label: "Queued", value: totals?.queued ?? 0, tone: "warning" as const },
      { id: "jobs-running", label: "Running", value: totals?.running ?? 0, tone: "primary" as const },
      { id: "jobs-completed", label: "Completed", value: totals?.completed ?? 0, tone: "success" as const },
      { id: "jobs-failed", label: "Failed", value: totals?.failed ?? 0, tone: "danger" as const },
    ];
    return applySliceHighlight(slices);
  }, [jobs?.totals, filters.selectedSliceId]);

  const timelineActivityChart: VizSlice[] = useMemo(() => {
    const series = run?.trends?.timeline_events ?? run?.trends?.cases_opened ?? [];
    if (series.length) {
      return applySliceHighlight(
        series.map((point) => ({
          id: `timeline-${point.index}`,
          label: point.label,
          value: point.value,
          tone: "info" as const,
        })),
      );
    }
    return applySliceHighlight(
      filteredCases.slice(0, 8).map((item, index) => ({
        id: `timeline-case-${item.id}`,
        label: item.case_number,
        value: index + 1,
        tone: "info" as const,
      })),
    );
  }, [filteredCases, filters.selectedSliceId, run?.trends]);

  const riskChart: VizSlice[] = useMemo(() => {
    const counts: Record<CasePriority, number> = {
      LOW: 0,
      MEDIUM: 0,
      HIGH: 0,
      CRITICAL: 0,
    };
    for (const item of filteredCases) {
      counts[item.priority] += 1;
    }
    const slices: VizSlice[] = [
      { id: "risk-LOW", label: "Low", value: counts.LOW, tone: "success" },
      { id: "risk-MEDIUM", label: "Medium", value: counts.MEDIUM, tone: "info" },
      { id: "risk-HIGH", label: "High", value: counts.HIGH, tone: "warning" },
      {
        id: "risk-CRITICAL",
        label: "Critical",
        value: counts.CRITICAL,
        tone: "danger",
      },
    ];
    return applySliceHighlight(slices);
  }, [filteredCases, filters.selectedSliceId]);

  const aiVerdictChart: VizSlice[] = useMemo(() => {
    const verdicts = asRecord(aiSection.verdicts ?? aiSection.ai_verdicts);
    const entries = Object.entries(verdicts)
      .filter(([, v]) => typeof v === "number")
      .map(([label, value]) => ({
        id: `verdict-${label}`,
        label,
        value: value as number,
        tone: "primary" as const,
      }));
    if (entries.length) return applySliceHighlight(entries);
    const completed = sectionNumber(aiSection, "analyses_completed");
    return applySliceHighlight(
      completed > 0
        ? [
            {
              id: "verdict-completed",
              label: "Analyses completed",
              value: completed,
              tone: "primary",
            },
          ]
        : [],
    );
  }, [aiSection, filters.selectedSliceId]);

  const fusionChart: VizSlice[] = useMemo(() => {
    const verdicts = asRecord(aiSection.fusion_verdicts);
    const entries = Object.entries(verdicts)
      .filter(([, v]) => typeof v === "number")
      .map(([label, value]) => ({
        id: `fusion-${label}`,
        label,
        value: value as number,
        tone: "warning" as const,
      }));
    if (entries.length) return applySliceHighlight(entries);
    const runs =
      metrics?.fusion_run_count ?? sectionNumber(aiSection, "fusion_runs");
    return applySliceHighlight(
      runs > 0
        ? [{ id: "fusion-runs", label: "Fusion runs", value: runs, tone: "warning" }]
        : [],
    );
  }, [aiSection, filters.selectedSliceId, metrics?.fusion_run_count]);

  const correlationChart: VizSlice[] = useMemo(() => {
    const slices = correlationEntries.map((e) => ({
      id: `corr-${e.label}`,
      label: e.label,
      value: e.value,
      tone: "success" as const,
    }));
    return applySliceHighlight(applyCorrelationFilter(slices));
  }, [correlationEntries, filters.correlationType, filters.selectedSliceId]);

  const reportChart: VizSlice[] = useMemo(() => {
    const series = run?.trends?.reports_generated ?? [];
    if (series.length) {
      return applySliceHighlight(
        series.map((point) => ({
          id: `report-${point.index}`,
          label: point.label,
          value: point.value,
          tone: "danger" as const,
        })),
      );
    }
    const count =
      metrics?.report_count ??
      sectionNumber(casesSection, "reports_generated");
    return applySliceHighlight(
      count > 0
        ? [
            {
              id: "reports-generated",
              label: "Generated",
              value: count,
              tone: "danger",
            },
          ]
        : [],
    );
  }, [
    casesSection,
    filters.selectedSliceId,
    metrics?.report_count,
    run?.trends,
  ]);

  const riskHeatmap: HeatCell[] = useMemo(
    () =>
      riskChart.map((slice) => ({
        id: slice.id,
        label: slice.label,
        value: slice.value,
        tone:
          slice.tone === "danger"
            ? "danger"
            : slice.tone === "warning"
              ? "warning"
              : slice.tone === "success"
                ? "success"
                : "info",
      })),
    [riskChart],
  );

  const activityHeatmap: HeatCell[] = useMemo(() => {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const buckets = days.map((label) => ({ label, value: 0 }));
    for (const item of filteredCases) {
      const day = new Date(item.updated_at).getDay();
      const index = day === 0 ? 6 : day - 1;
      buckets[index].value += 1;
    }
    return buckets.map((b, i) => ({
      id: `activity-${i}`,
      label: b.label,
      value: b.value,
      tone: "primary" as const,
    }));
  }, [filteredCases]);

  const evidenceDensityHeatmap: HeatCell[] = useMemo(
    () =>
      evidenceBreakdown.map((e) => ({
        id: `density-${e.label}`,
        label: e.label,
        value: e.value,
        tone: "info" as const,
      })),
    [evidenceBreakdown],
  );

  const processingLoadHeatmap: HeatCell[] = useMemo(
    () =>
      processingJobsChart.map((s) => ({
        id: s.id,
        label: s.label,
        value: s.value,
        tone:
          s.tone === "danger"
            ? "danger"
            : s.tone === "warning"
              ? "warning"
              : s.tone === "success"
                ? "success"
                : "primary",
      })),
    [processingJobsChart],
  );

  const graph = useMemo(() => {
    const nodes: GraphNode[] = [];
    const edges: GraphEdge[] = [];
    const caseNodes = filteredCases.slice(0, 8);
    for (const item of caseNodes) {
      nodes.push({
        id: `case-${item.id}`,
        label: item.case_number,
        kind: "case",
        detail: `${item.title} · ${item.priority}`,
      });
    }
    evidenceBreakdown.slice(0, 6).forEach((e, index) => {
      const id = `evidence-${e.label}`;
      nodes.push({
        id,
        label: e.label,
        kind: "evidence",
        detail: `${e.value} items`,
      });
      if (caseNodes[index % Math.max(caseNodes.length, 1)]) {
        const caseId = caseNodes[index % caseNodes.length].id;
        edges.push({
          id: `e-${id}-${caseId}`,
          source: `case-${caseId}`,
          target: id,
          label: "contains",
        });
      }
    });
    const fusionRuns =
      metrics?.fusion_run_count ?? sectionNumber(aiSection, "fusion_runs");
    if (fusionRuns > 0) {
      nodes.push({
        id: "fusion-hub",
        label: `Fusion ×${fusionRuns}`,
        kind: "fusion",
        detail: "Cross-modal fusion",
      });
      for (const item of caseNodes.slice(0, 3)) {
        edges.push({
          id: `f-${item.id}`,
          source: `case-${item.id}`,
          target: "fusion-hub",
        });
      }
    }
    const corr =
      metrics?.correlation_count ?? sectionNumber(aiSection, "correlations");
    if (corr > 0) {
      nodes.push({
        id: "corr-hub",
        label: `Corr ×${corr}`,
        kind: "correlation",
        detail: "Correlation matches",
      });
      edges.push({
        id: "corr-link",
        source: "fusion-hub",
        target: "corr-hub",
      });
    }
    const reports =
      metrics?.report_count ?? sectionNumber(casesSection, "reports_generated");
    if (reports > 0) {
      nodes.push({
        id: "report-hub",
        label: `Reports ×${reports}`,
        kind: "report",
        detail: "Generated reports",
      });
      if (caseNodes[0]) {
        edges.push({
          id: "report-link",
          source: `case-${caseNodes[0].id}`,
          target: "report-hub",
        });
      }
    }
    const timelines = metrics?.timeline_count ?? 0;
    if (timelines > 0) {
      nodes.push({
        id: "timeline-hub",
        label: `Timelines ×${timelines}`,
        kind: "timeline",
        detail: "Timeline reconstructions",
      });
      if (caseNodes[0]) {
        edges.push({
          id: "timeline-link",
          source: `case-${caseNodes[0].id}`,
          target: "timeline-hub",
        });
      }
    }
    // Drop dangling edges when fusion hub missing
    const nodeIds = new Set(nodes.map((n) => n.id));
    return {
      nodes,
      edges: edges.filter(
        (e) => nodeIds.has(e.source) && nodeIds.has(e.target),
      ),
    };
  }, [
    aiSection,
    casesSection,
    evidenceBreakdown,
    filteredCases,
    metrics,
  ]);

  const widgets = useMemo(() => {
    const topRisks: InsightItem[] = filteredCases
      .filter((c) => c.priority === "HIGH" || c.priority === "CRITICAL")
      .slice(0, 5)
      .map((c) => ({
        id: c.id,
        title: c.case_number,
        detail: `${c.title} · ${c.priority}`,
        href: `/investigations/${c.id}`,
        tone: c.priority === "CRITICAL" ? "error" : "warning",
      }));

    const alerts = sectionNumber(integritySection, "alerts");
    const latestFindings: InsightItem[] =
      alerts > 0
        ? [
            {
              id: "integrity-alerts",
              title: `${alerts} integrity alert(s)`,
              detail: "From analytics integrity section",
              tone: "warning",
            },
          ]
        : [];

    const reportCount =
      metrics?.report_count ?? sectionNumber(casesSection, "reports_generated");
    const recentReports: InsightItem[] =
      reportCount > 0
        ? [
            {
              id: "reports",
              title: `${reportCount} report(s)`,
              detail: "Report registry total",
              tone: "primary",
            },
          ]
        : [];

    const recentCorrelations: InsightItem[] = correlationEntries
      .slice(0, 5)
      .map((e) => ({
        id: e.label,
        title: e.label,
        detail: `${e.value} match(es)`,
        tone: "success",
      }));

    const fusionRuns =
      metrics?.fusion_run_count ?? sectionNumber(aiSection, "fusion_runs");
    const fusionSummary: InsightItem[] =
      fusionRuns > 0
        ? [
            {
              id: "fusion",
              title: `${fusionRuns} fusion run(s)`,
              detail: "Persisted fusion executions",
              tone: "warning",
            },
          ]
        : [];

    const timelineSummary: InsightItem[] =
      (metrics?.timeline_count ?? 0) > 0
        ? [
            {
              id: "timelines",
              title: `${metrics?.timeline_count} timeline(s)`,
              detail: "Reconstructed investigations",
              tone: "info",
            },
          ]
        : [];

    const mostActiveCases: InsightItem[] = [...filteredCases]
      .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
      .slice(0, 5)
      .map((c) => ({
        id: c.id,
        title: c.case_number,
        detail: `Updated ${new Date(c.updated_at).toLocaleString()}`,
        href: `/investigations/${c.id}`,
        tone: "neutral",
      }));

    return {
      topRisks,
      latestFindings,
      recentReports,
      recentCorrelations,
      fusionSummary,
      timelineSummary,
      mostActiveCases,
    };
  }, [
    aiSection,
    casesSection,
    correlationEntries,
    filteredCases,
    integritySection,
    metrics,
  ]);

  const caseOptions = cases.map((c: CaseRecord) => ({
    id: c.id,
    label: `${c.case_number} · ${c.title}`,
  }));

  const confidenceOk =
    filters.confidenceMin <= 0 ||
    sectionNumber(aiSection, "average_confidence") >= filters.confidenceMin ||
    (typeof aiSection.average_confidence === "number" &&
      (aiSection.average_confidence as number) >= filters.confidenceMin);

  return {
    analyticsQuery,
    casesQuery,
    metricsQuery,
    jobsQuery,
    filters,
    setFilters,
    caseOptions,
    evidenceTypes,
    modalities,
    correlationTypes: correlationEntries.map((e) => e.label),
    evidenceTypeChart: confidenceOk ? evidenceTypeChart : [],
    investigationProgressChart,
    processingJobsChart,
    timelineActivityChart,
    riskChart,
    aiVerdictChart,
    fusionChart,
    correlationChart,
    reportChart,
    riskHeatmap,
    activityHeatmap,
    evidenceDensityHeatmap,
    processingLoadHeatmap,
    graph,
    widgets,
    loading: analyticsQuery.isPending && !analyticsQuery.data,
  };
}
