import { Panel } from "../ui/Panel";

function num(value: unknown): string {
  if (typeof value === "number") return String(value);
  if (value == null) return "n/a";
  return String(value);
}

interface ProcessingMetricsPanelProps {
  data: Record<string, unknown>;
}

export function ProcessingMetricsPanel({ data }: ProcessingMetricsPanelProps) {
  return (
    <Panel description="Jobs created, completed, retries, and runtimes." title="Processing Summary">
      <dl className="grid grid-cols-2 gap-3 p-4 text-xs">
        <div>
          <dt className="text-slate-500">Created</dt>
          <dd className="text-slate-200">{num(data.jobs_created)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Completed</dt>
          <dd className="text-slate-200">{num(data.jobs_completed)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Failures</dt>
          <dd className="text-slate-200">{num(data.failures)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Retries</dt>
          <dd className="text-slate-200">{num(data.retries)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Avg execution</dt>
          <dd className="text-slate-200">{num(data.execution_duration_avg_ms)} ms</dd>
        </div>
        <div>
          <dt className="text-slate-500">P95 execution</dt>
          <dd className="text-slate-200">{num(data.execution_duration_p95_ms)} ms</dd>
        </div>
        <div>
          <dt className="text-slate-500">Success rate</dt>
          <dd className="text-slate-200">{num(data.success_rate)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Failure rate</dt>
          <dd className="text-slate-200">{num(data.failure_rate)}</dd>
        </div>
      </dl>
    </Panel>
  );
}
