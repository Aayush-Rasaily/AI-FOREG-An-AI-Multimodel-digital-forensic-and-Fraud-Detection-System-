import { Panel } from "../ui/Panel";

interface ActivityTimelineProps {
  data: Record<string, unknown>;
}

export function ActivityTimeline({ data }: ActivityTimelineProps) {
  const events = Array.isArray(data.recent_events)
    ? (data.recent_events as Array<Record<string, unknown>>)
    : [];

  return (
    <Panel description="Recent operational audit events." title="Recent Activity">
      <div className="p-4">
        {events.length === 0 ? (
          <p className="text-xs text-slate-500">No recent activity.</p>
        ) : (
          <ul className="space-y-2">
            {events.map((event) => (
              <li
                className="rounded-lg border border-slate-800 px-3 py-2 text-xs"
                key={String(event.id)}
              >
                <p className="text-slate-200">{String(event.operation)}</p>
                <p className="mt-1 text-slate-500">
                  {String(event.user)} ·{" "}
                  {event.timestamp
                    ? new Date(String(event.timestamp)).toLocaleString()
                    : "n/a"}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Panel>
  );
}
