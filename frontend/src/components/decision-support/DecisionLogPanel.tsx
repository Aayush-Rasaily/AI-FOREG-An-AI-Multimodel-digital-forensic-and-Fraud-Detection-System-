import type { DecisionLogEntry } from "../../types/decisionSupport";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

interface DecisionLogPanelProps {
  decisions: DecisionLogEntry[];
}

export function DecisionLogPanel({ decisions }: DecisionLogPanelProps) {
  return (
    <Panel
      description="Investigator decisions with justification and provenance."
      title="Decision log"
    >
      <div className="space-y-3 p-4">
        {!decisions.length ? (
          <EmptyState
            description="No decisions have been recorded yet."
            title="No decisions"
          />
        ) : (
          decisions.map((item) => (
            <div
              className="rounded-lg border border-slate-800 p-3 text-xs text-slate-400"
              key={item.id}
            >
              <div className="mb-2 flex flex-wrap gap-2">
                <Badge tone="cyan">{item.decision_type}</Badge>
              </div>
              <p className="text-slate-200">{item.investigator}</p>
              <p className="mt-1">{item.justification}</p>
              <p className="mt-2 text-[11px] text-slate-600">
                {new Date(item.created_at).toLocaleString()}
              </p>
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
