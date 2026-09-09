import { Panel } from "../ui/Panel";

interface AuditAnalyticsPanelProps {
  data: Record<string, unknown>;
}

export function AuditAnalyticsPanel({ data }: AuditAnalyticsPanelProps) {
  const investigators = Array.isArray(data.busiest_investigators)
    ? (data.busiest_investigators as Array<Record<string, unknown>>)
    : [];
  const inactive = Array.isArray(data.inactive_investigations)
    ? (data.inactive_investigations as Array<Record<string, unknown>>)
    : [];

  return (
    <Panel description="Busiest users, inactive cases, and report stats." title="Audit Analytics">
      <div className="grid gap-4 p-4 text-xs md:grid-cols-2">
        <div>
          <p className="mb-1 text-muted">Busiest investigators</p>
          {investigators.length === 0 ? (
            <p className="text-muted">No activity yet.</p>
          ) : (
            <ul className="space-y-1">
              {investigators.slice(0, 5).map((item) => (
                <li key={String(item.user)} className="text-muted">
                  {String(item.user)} · {String(item.event_count)}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <p className="mb-1 text-muted">Inactive investigations</p>
          {inactive.length === 0 ? (
            <p className="text-muted">None past inactivity threshold.</p>
          ) : (
            <ul className="space-y-1">
              {inactive.slice(0, 5).map((item) => (
                <li key={String(item.case_id)} className="text-muted">
                  {String(item.case_number ?? item.case_id)}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Panel>
  );
}
