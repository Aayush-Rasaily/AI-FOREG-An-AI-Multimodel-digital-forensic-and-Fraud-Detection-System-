import { ListChecks } from "lucide-react";

import { FindingCard } from "../findings/FindingCard";
import { Panel } from "../ui/Panel";

export function FindingsPanel() {
  return (
    <Panel
      description="Only engine-backed observations will be shown."
      title="Findings"
    >
      <div className="space-y-3 p-4">
        <FindingCard />
        <div className="flex items-center gap-2 text-[11px] text-slate-600">
          <ListChecks aria-hidden="true" size={14} />
          Findings remain empty until analysis is connected.
        </div>
      </div>
    </Panel>
  );
}

