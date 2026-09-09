import type { Hypothesis } from "../../types/investigationIntelligence";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

interface HypothesisPanelProps {
  hypotheses: Hypothesis[];
  search: string;
  priorityFilter: string;
}

export function HypothesisPanel({
  hypotheses,
  search,
  priorityFilter,
}: HypothesisPanelProps) {
  const query = search.trim().toLowerCase();
  const visible = hypotheses.filter((item) => {
    const matchesPriority =
      priorityFilter === "all" || item.priority === priorityFilter;
    const matchesSearch =
      query.length === 0 ||
      item.title.toLowerCase().includes(query) ||
      item.hypothesis_type.toLowerCase().includes(query) ||
      item.explanation.toLowerCase().includes(query);
    return matchesPriority && matchesSearch;
  });

  return (
    <Panel description="Ranked deterministic hypotheses." title="Hypotheses">
      <div className="space-y-3 p-4">
        {!visible.length ? (
          <EmptyState
            description="No hypotheses match the current filters."
            title="No hypotheses"
          />
        ) : (
          visible.map((item) => (
            <div
              className="rounded-lg border border-border p-3 text-xs text-muted"
              key={item.hypothesis_key}
            >
              <div className="mb-2 flex flex-wrap gap-2">
                <Badge tone="primary">{item.priority}</Badge>
                <Badge tone="neutral">{item.status}</Badge>
                <Badge tone="neutral">
                  {(item.confidence * 100).toFixed(0)}% confidence
                </Badge>
              </div>
              <p className="text-sm text-foreground">{item.title}</p>
              <p className="mt-1">{item.explanation}</p>
              {item.supporting_evidence_ids.length ? (
                <p className="mt-2 font-mono text-[11px] text-muted">
                  Support: {item.supporting_evidence_ids.join(", ")}
                </p>
              ) : null}
              {item.contradicting_evidence_ids.length ? (
                <p className="mt-1 font-mono text-[11px] text-danger/80">
                  Contradict: {item.contradicting_evidence_ids.join(", ")}
                </p>
              ) : null}
              {item.provenance ? (
                <p className="mt-2 text-[11px] text-subtle">
                  Provenance engine{" "}
                  {String(item.provenance.engine_version ?? "—")}
                </p>
              ) : null}
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
