import { lazy, Suspense } from "react";

import { useInteractiveAnalytics } from "../../hooks/useInteractiveAnalytics";
import { AnalyticsFilterBar } from "./AnalyticsFilterBar";
import { AnalyticsInsightWidgets } from "./AnalyticsInsightWidgets";
import { HeatmapGrid } from "./HeatmapGrid";
import { InteractiveBarChart } from "./InteractiveBarChart";
import { VizSkeleton } from "./VizSkeleton";
import type { VizSlice } from "./types";

const RelationshipGraph = lazy(() =>
  import("./RelationshipGraph").then((m) => ({ default: m.RelationshipGraph })),
);

function selectSlice(
  setFilters: ReturnType<typeof useInteractiveAnalytics>["setFilters"],
  slice: VizSlice | null,
) {
  setFilters((current) => ({
    ...current,
    selectedSliceId: slice?.id ?? null,
  }));
}

export function InteractiveAnalyticsWorkspace() {
  const data = useInteractiveAnalytics();

  if (data.loading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <VizSkeleton />
        <VizSkeleton />
        <VizSkeleton />
        <VizSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <AnalyticsFilterBar
        caseOptions={data.caseOptions}
        correlationTypes={data.correlationTypes}
        evidenceTypes={data.evidenceTypes}
        filters={data.filters}
        modalities={data.modalities}
        onChange={data.setFilters}
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <InteractiveBarChart
          description="Click legend or bars to filter"
          exportName="evidence-types"
          onSelect={(slice) => selectSlice(data.setFilters, slice)}
          selectedId={data.filters.selectedSliceId}
          slices={data.evidenceTypeChart}
          title="Evidence types"
        />
        <InteractiveBarChart
          description="Case lifecycle progress"
          exportName="investigation-progress"
          onSelect={(slice) => selectSlice(data.setFilters, slice)}
          selectedId={data.filters.selectedSliceId}
          slices={data.investigationProgressChart}
          title="Investigation progress"
        />
        <InteractiveBarChart
          description="Queue and worker outcomes"
          exportName="processing-jobs"
          onSelect={(slice) => selectSlice(data.setFilters, slice)}
          selectedId={data.filters.selectedSliceId}
          slices={data.processingJobsChart}
          title="Processing jobs"
        />
        <InteractiveBarChart
          description="Deterministic activity series"
          exportName="timeline-activity"
          onSelect={(slice) => selectSlice(data.setFilters, slice)}
          selectedId={data.filters.selectedSliceId}
          slices={data.timelineActivityChart}
          title="Timeline activity"
        />
        <InteractiveBarChart
          description="Priority distribution"
          exportName="risk-distribution"
          onSelect={(slice) => selectSlice(data.setFilters, slice)}
          selectedId={data.filters.selectedSliceId}
          slices={data.riskChart}
          title="Risk distribution"
        />
        <InteractiveBarChart
          description="AI outcome aggregates"
          exportName="ai-verdicts"
          onSelect={(slice) => selectSlice(data.setFilters, slice)}
          selectedId={data.filters.selectedSliceId}
          slices={data.aiVerdictChart}
          title="AI verdict distribution"
        />
        <InteractiveBarChart
          description="Cross-modal fusion"
          exportName="fusion-results"
          onSelect={(slice) => selectSlice(data.setFilters, slice)}
          selectedId={data.filters.selectedSliceId}
          slices={data.fusionChart}
          title="Fusion results"
        />
        <InteractiveBarChart
          description="Relationship match types"
          exportName="correlation-types"
          onSelect={(slice) => selectSlice(data.setFilters, slice)}
          selectedId={data.filters.selectedSliceId}
          slices={data.correlationChart}
          title="Correlation types"
        />
        <InteractiveBarChart
          description="Report generation"
          exportName="report-statistics"
          onSelect={(slice) => selectSlice(data.setFilters, slice)}
          selectedId={data.filters.selectedSliceId}
          slices={data.reportChart}
          title="Report statistics"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <HeatmapGrid
          cells={data.riskHeatmap}
          columns={2}
          description="Case priority intensity"
          onSelect={(cell) =>
            data.setFilters((current) => ({
              ...current,
              risk:
                cell.label.toUpperCase() === "LOW" ||
                cell.label.toUpperCase() === "MEDIUM" ||
                cell.label.toUpperCase() === "HIGH" ||
                cell.label.toUpperCase() === "CRITICAL"
                  ? cell.label.toUpperCase()
                  : current.risk,
              selectedSliceId: cell.id,
            }))
          }
          selectedId={data.filters.selectedSliceId}
          title="Risk heatmap"
        />
        <HeatmapGrid
          cells={data.activityHeatmap}
          columns={4}
          description="Case updates by weekday"
          title="Activity heatmap"
        />
        <HeatmapGrid
          cells={data.evidenceDensityHeatmap}
          columns={2}
          description="Evidence volume by type"
          title="Evidence density"
        />
        <HeatmapGrid
          cells={data.processingLoadHeatmap}
          columns={2}
          description="Worker queue load"
          title="Processing load"
        />
      </div>

      <Suspense fallback={<VizSkeleton label="Loading relationship graph" />}>
        <RelationshipGraph
          edges={data.graph.edges}
          nodes={data.graph.nodes}
        />
      </Suspense>

      <AnalyticsInsightWidgets {...data.widgets} />
    </div>
  );
}
