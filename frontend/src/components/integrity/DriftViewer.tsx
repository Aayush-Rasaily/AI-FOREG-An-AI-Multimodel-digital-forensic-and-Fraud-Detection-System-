import type { IntegrityDrift } from "../../types/integrity";
import { Panel } from "../ui/Panel";

interface DriftViewerProps {
  drifts: IntegrityDrift[];
}

export function DriftViewer({ drifts }: DriftViewerProps) {
  return (
    <Panel
      description="Field drift vs the prior integrity monitor snapshot."
      title="Drift Viewer"
    >
      <div className="space-y-3 p-4">
        {drifts.length === 0 ? (
          <p className="text-xs text-muted">No drift detected.</p>
        ) : null}
        {drifts.map((item) => (
          <div
            className="border-b border-border/80 pb-2 text-xs last:border-0"
            key={item.drift_key}
          >
            <p className="text-foreground">
              {item.field_name} · evidence {item.evidence_id}
            </p>
            <p className="mt-1 text-muted">{item.message}</p>
            <p className="mt-1 font-mono text-[11px] text-subtle">
              prev {(item.previous_value ?? "—").slice(0, 24)} → curr{" "}
              {(item.current_value ?? "—").slice(0, 24)}
            </p>
          </div>
        ))}
      </div>
    </Panel>
  );
}
