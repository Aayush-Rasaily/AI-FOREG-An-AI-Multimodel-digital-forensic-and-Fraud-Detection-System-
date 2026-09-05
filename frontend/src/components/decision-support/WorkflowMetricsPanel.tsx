import type { WorkloadMetrics } from "../../types/decisionSupport";
import { Panel } from "../ui/Panel";

interface WorkflowMetricsPanelProps {
  metrics: WorkloadMetrics | null;
  currentStage: string | null;
}

function pct(value: number) {
  return `${(value * 100).toFixed(0)}%`;
}

export function WorkflowMetricsPanel({
  metrics,
  currentStage,
}: WorkflowMetricsPanelProps) {
  if (!metrics) {
    return (
      <Panel description="Workload and progress metrics." title="Metrics">
        <div className="p-4 text-xs text-slate-500">No metrics yet.</div>
      </Panel>
    );
  }

  const rows: Array<[string, string]> = [
    ["Current stage", currentStage ?? "—"],
    ["Open tasks", String(metrics.open_tasks)],
    ["Completed tasks", String(metrics.completed_tasks)],
    ["Pending reviews", String(metrics.pending_reviews)],
    ["Average priority", metrics.average_priority.toFixed(2)],
    ["Critical evidence", String(metrics.critical_evidence_count)],
    ["Workflow completion", pct(metrics.workflow_completion)],
    ["Investigation progress", pct(metrics.investigation_progress)],
    ["Evidence review coverage", pct(metrics.evidence_review_coverage)],
  ];

  return (
    <Panel description="Workload and progress metrics." title="Metrics">
      <div className="space-y-2 p-4 text-xs text-slate-400">
        <dl className="grid gap-2 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt className="text-slate-600">{label}</dt>
              <dd className="text-slate-200">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </Panel>
  );
}
