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
          <dt className="text-muted">Created</dt>
          <dd className="text-foreground">{num(data.jobs_created)}</dd>
        </div>
        <div>
          <dt className="text-muted">Completed</dt>
          <dd className="text-foreground">{num(data.jobs_completed)}</dd>
        </div>
        <div>
          <dt className="text-muted">Failures</dt>
          <dd className="text-foreground">{num(data.failures)}</dd>
        </div>
        <div>
          <dt className="text-muted">Retries</dt>
          <dd className="text-foreground">{num(data.retries)}</dd>
        </div>
        <div>
          <dt className="text-muted">Avg execution</dt>
          <dd className="text-foreground">{num(data.execution_duration_avg_ms)} ms</dd>
        </div>
        <div>
          <dt className="text-muted">P95 execution</dt>
          <dd className="text-foreground">{num(data.execution_duration_p95_ms)} ms</dd>
        </div>
        <div>
          <dt className="text-muted">Success rate</dt>
          <dd className="text-foreground">{num(data.success_rate)}</dd>
        </div>
        <div>
          <dt className="text-muted">Failure rate</dt>
          <dd className="text-foreground">{num(data.failure_rate)}</dd>
        </div>
      </dl>
    </Panel>
  );
}
