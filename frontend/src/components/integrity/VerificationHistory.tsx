import type { IntegrityHistoryItem } from "../../types/integrity";
import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";

interface VerificationHistoryProps {
  items: IntegrityHistoryItem[];
}

export function VerificationHistory({ items }: VerificationHistoryProps) {
  return (
    <Panel
      description="Prior integrity monitor runs for this case."
      title="Verification History"
    >
      <div className="space-y-3 p-4">
        {items.length === 0 ? (
          <p className="text-xs text-slate-500">No verification history.</p>
        ) : null}
        {items.map((item) => (
          <div
            className="border-b border-slate-800/80 pb-2 text-xs last:border-0"
            key={item.id}
          >
            <div className="flex flex-wrap gap-2">
              <Badge tone="cyan">{item.status}</Badge>
              <span className="text-slate-500">
                {new Date(item.created_at).toLocaleString()}
              </span>
            </div>
            <p className="mt-1 text-slate-500">
              Checks {item.check_count} · Alerts {item.alert_count} · Drift{" "}
              {item.drift_count} · Score{" "}
              {(item.metrics.integrity_score * 100).toFixed(0)}% · engine{" "}
              {item.engine_version}
            </p>
          </div>
        ))}
      </div>
    </Panel>
  );
}
