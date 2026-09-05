import type { IntegrityRun } from "../../types/integrity";
import { Panel } from "../ui/Panel";

interface IntegrityTimelineProps {
  timeline: IntegrityRun["timeline"];
}

export function IntegrityTimeline({ timeline }: IntegrityTimelineProps) {
  return (
    <Panel
      description="Per-evidence evaluation timeline from the latest run."
      title="Integrity Timeline"
    >
      <div className="space-y-3 p-4">
        {timeline.length === 0 ? (
          <p className="text-xs text-slate-500">No timeline events.</p>
        ) : null}
        {timeline.map((item, index) => (
          <div
            className="border-b border-slate-800/80 pb-2 text-xs last:border-0"
            key={`${String(item.evidence_id)}-${index}`}
          >
            <p className="text-slate-200">
              {String(item.event ?? "event")} · evidence{" "}
              {String(item.evidence_id ?? "—")}
            </p>
            <p className="mt-1 text-slate-500">
              Custody {String(item.custody_events ?? 0)} · Storage{" "}
              {String(item.storage_present ?? "n/a")}
            </p>
          </div>
        ))}
      </div>
    </Panel>
  );
}
