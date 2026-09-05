import type { ValidationMetrics } from "../../types/caseReview";
import { Panel } from "../ui/Panel";

interface ReviewMetricsPanelProps {
  metrics: ValidationMetrics | null;
  stage: string | null;
  outstanding: string[];
  blocking: string[];
}

function pct(value: number) {
  return `${(value * 100).toFixed(0)}%`;
}

export function ReviewMetricsPanel({
  metrics,
  stage,
  outstanding,
  blocking,
}: ReviewMetricsPanelProps) {
  if (!metrics) {
    return (
      <Panel description="Validation and approval metrics." title="Metrics">
        <div className="p-4 text-xs text-slate-500">No metrics yet.</div>
      </Panel>
    );
  }

  const rows: Array<[string, string]> = [
    ["Stage", stage ?? "—"],
    ["Validation", pct(metrics.validation_pct)],
    ["Evidence coverage", pct(metrics.evidence_coverage_pct)],
    ["Review completion", pct(metrics.review_completion_pct)],
    ["Approval completion", pct(metrics.approval_completion_pct)],
    ["Outstanding issues", String(metrics.outstanding_issues)],
    ["Blocking issues", String(metrics.blocking_issues)],
  ];

  return (
    <Panel description="Validation and approval metrics." title="Metrics">
      <div className="space-y-3 p-4 text-xs text-slate-400">
        <dl className="grid gap-2 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt className="text-slate-600">{label}</dt>
              <dd className="text-slate-200">{value}</dd>
            </div>
          ))}
        </dl>
        {blocking.length > 0 ? (
          <div>
            <p className="text-slate-500">Blocking</p>
            <ul className="mt-1 list-disc pl-4 text-rose-300">
              {blocking.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {outstanding.length > 0 ? (
          <div>
            <p className="text-slate-500">Outstanding</p>
            <ul className="mt-1 list-disc pl-4 text-amber-200/80">
              {outstanding.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </Panel>
  );
}
