import type { IntegrityAlert } from "../../types/integrity";
import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";

interface AlertPanelProps {
  alerts: IntegrityAlert[];
  search: string;
}

export function AlertPanel({ alerts, search }: AlertPanelProps) {
  const needle = search.trim().toLowerCase();
  const filtered = alerts.filter((item) => {
    if (!needle) return true;
    return (
      item.title.toLowerCase().includes(needle) ||
      item.message.toLowerCase().includes(needle) ||
      (item.evidence_id ?? "").toLowerCase().includes(needle)
    );
  });

  return (
    <Panel description="Alerts from failed or warned integrity checks." title="Alerts">
      <div className="space-y-3 p-4">
        {filtered.length === 0 ? (
          <p className="text-xs text-slate-500">No alerts.</p>
        ) : null}
        {filtered.map((item) => (
          <div
            className="border-b border-slate-800/80 pb-2 text-xs last:border-0"
            key={item.alert_key}
          >
            <div className="flex flex-wrap gap-2">
              <Badge
                tone={
                  item.severity === "CRITICAL" || item.severity === "HIGH"
                    ? "red"
                    : item.severity === "MEDIUM"
                      ? "amber"
                      : "neutral"
                }
              >
                {item.severity}
              </Badge>
              <span className="text-slate-200">{item.title}</span>
            </div>
            <p className="mt-1 text-slate-500">{item.message}</p>
            {item.evidence_id ? (
              <p className="mt-1 text-[11px] text-slate-600">
                Evidence {item.evidence_id}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </Panel>
  );
}
