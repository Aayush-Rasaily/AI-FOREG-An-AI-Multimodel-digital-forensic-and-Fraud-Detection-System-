import { Activity, Layers3, PlayCircle } from "lucide-react";

import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

export function AnalysisPanel() {
  return (
    <Panel title="Analysis panel">
      <div className="p-4">
        <EmptyState
          className="min-h-48 rounded-lg border border-dashed border-slate-800"
          description="Analysis orchestration, engine selection, and job provenance will become available in a later phase."
          icon={<Layers3 aria-hidden="true" size={19} />}
          title="Analysis engine not connected"
        />
        <div className="mt-4 grid grid-cols-2 gap-2">
          <Button disabled size="sm" variant="secondary">
            <PlayCircle aria-hidden="true" size={14} />
            Run analysis
          </Button>
          <Button disabled size="sm" variant="ghost">
            <Activity aria-hidden="true" size={14} />
            View jobs
          </Button>
        </div>
      </div>
    </Panel>
  );
}

