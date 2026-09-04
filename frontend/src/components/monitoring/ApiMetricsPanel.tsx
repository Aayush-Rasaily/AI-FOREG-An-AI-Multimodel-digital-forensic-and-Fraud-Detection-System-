import { Panel } from "../ui/Panel";

interface ApiMetricsPanelProps {
  data: Record<string, unknown>;
}

export function ApiMetricsPanel({ data }: ApiMetricsPanelProps) {
  const endpoints = Array.isArray(data.endpoint_usage)
    ? (data.endpoint_usage as Array<Record<string, unknown>>)
    : [];

  return (
    <Panel
      description="API usage derived from persisted audit operations."
      title="API Usage"
    >
      <div className="space-y-3 p-4 text-xs">
        <p className="text-slate-400">
          Request counts: {String(data.request_counts ?? 0)} · Source:{" "}
          {String(data.source ?? "audit_events")}
        </p>
        {endpoints.length === 0 ? (
          <p className="text-slate-500">No audited API operations yet.</p>
        ) : (
          <ul className="space-y-1">
            {endpoints.slice(0, 8).map((item) => (
              <li
                className="flex justify-between text-slate-300"
                key={String(item.operation)}
              >
                <span className="truncate pr-2">{String(item.operation)}</span>
                <span>{String(item.count)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Panel>
  );
}
