import type { EvidenceGap } from "../../types/investigationIntelligence";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

interface EvidenceGapPanelProps {
  gaps: EvidenceGap[];
  search: string;
}

export function EvidenceGapPanel({ gaps, search }: EvidenceGapPanelProps) {
  const query = search.trim().toLowerCase();
  const visible = gaps.filter(
    (item) =>
      query.length === 0 ||
      item.gap_type.toLowerCase().includes(query) ||
      item.reason.toLowerCase().includes(query),
  );

  return (
    <Panel description="Missing analysis and corroboration gaps." title="Evidence gaps">
      <div className="space-y-3 p-4">
        {!visible.length ? (
          <EmptyState
            description="No evidence gaps were identified."
            title="No gaps"
          />
        ) : (
          visible.map((item) => (
            <div
              className="rounded-lg border border-slate-800 p-3 text-xs text-slate-400"
              key={item.gap_key}
            >
              <div className="mb-2 flex flex-wrap gap-2">
                <Badge tone="cyan">{item.severity}</Badge>
                <Badge tone="neutral">{item.gap_type}</Badge>
              </div>
              <p className="text-slate-200">{item.reason}</p>
              <p className="mt-1 text-slate-500">
                Action: {item.recommended_action}
              </p>
              {item.affected_evidence_ids.length ? (
                <p className="mt-2 font-mono text-[11px] text-slate-500">
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
