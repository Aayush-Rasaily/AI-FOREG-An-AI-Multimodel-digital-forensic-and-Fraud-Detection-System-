import type { IntelligenceRecommendation } from "../../types/investigationIntelligence";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

interface RecommendationsPanelProps {
  recommendations: IntelligenceRecommendation[];
  search: string;
}

export function RecommendationsPanel({
  recommendations,
  search,
}: RecommendationsPanelProps) {
  const query = search.trim().toLowerCase();
  const visible = recommendations.filter(
    (item) =>
      query.length === 0 ||
      item.code.toLowerCase().includes(query) ||
      item.action_text.toLowerCase().includes(query),
  );

  return (
    <Panel
      description="Fixed-template recommended next actions."
      title="Recommendations"
    >
      <div className="space-y-3 p-4">
        {!visible.length ? (
          <EmptyState
            description="No recommendations for this run."
            title="No recommendations"
          />
        ) : (
          visible.map((item) => (
            <div
              className="rounded-lg border border-border p-3 text-xs text-muted"
              key={item.recommendation_key}
            >
              <div className="mb-2 flex flex-wrap gap-2">
                <Badge tone="primary">{item.priority}</Badge>
                <Badge tone="neutral">{item.code}</Badge>
              </div>
              <p className="text-sm text-foreground">{item.action_text}</p>
              {item.affected_evidence_ids.length ? (
                <p className="mt-2 font-mono text-[11px] text-muted">
                  Evidence: {item.affected_evidence_ids.join(", ")}
                </p>
              ) : null}
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
