import type { CaseReviewHistoryItem } from "../../types/caseReview";
import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";

interface ReviewHistoryPanelProps {
  items: CaseReviewHistoryItem[];
}

export function ReviewHistoryPanel({ items }: ReviewHistoryPanelProps) {
  return (
    <Panel
      description="Prior case review runs for this investigation."
      title="Review History"
    >
      <div className="space-y-3 p-4">
        {items.length === 0 ? (
          <p className="text-xs text-muted">No review history yet.</p>
        ) : null}
        {items.map((item) => (
          <div
            className="border-b border-border/80 pb-2 text-xs last:border-0"
            key={item.id}
          >
            <div className="flex flex-wrap gap-2">
              <Badge tone="neutral">{item.stage}</Badge>
              <Badge tone="primary">{item.status}</Badge>
              <span className="text-muted">
                {new Date(item.created_at).toLocaleString()}
              </span>
            </div>
            <p className="mt-1 text-muted">
              Checklist {item.checklist_count} · Approvals {item.approval_count}{" "}
              · Validation {(item.metrics.validation_pct * 100).toFixed(0)}% ·
              engine {item.engine_version}
            </p>
          </div>
        ))}
      </div>
    </Panel>
  );
}
