import type { ReviewQueueItem } from "../../types/decisionSupport";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

interface ReviewQueuePanelProps {
  items: ReviewQueueItem[];
  search: string;
}

export function ReviewQueuePanel({ items, search }: ReviewQueuePanelProps) {
  const query = search.trim().toLowerCase();
  const visible = items.filter(
    (item) =>
      query.length === 0 ||
      item.evidence_id.toLowerCase().includes(query) ||
      item.reasons.some((reason) => reason.toLowerCase().includes(query)),
  );

  return (
    <Panel
      description="Prioritized evidence requiring investigator review."
      title="Review queue"
    >
      <div className="space-y-3 p-4">
        {!visible.length ? (
          <EmptyState
            description="No evidence is currently queued for review."
            title="Queue empty"
          />
        ) : (
          visible.map((item) => (
            <div
              className="rounded-lg border border-slate-800 p-3 text-xs text-slate-400"
              key={item.queue_key}
            >
              <div className="mb-2 flex flex-wrap gap-2">
                <Badge tone="cyan">{item.priority}</Badge>
                <Badge tone="neutral">
                  {(item.priority_score * 100).toFixed(0)}%
                </Badge>
              </div>
              <p className="font-mono text-slate-200">{item.evidence_id}</p>
              <p className="mt-1">{item.reasons.join(", ")}</p>
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
