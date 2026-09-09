import { Database, Fingerprint } from "lucide-react";

import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

export function MetadataPanel() {
  return (
    <Panel title="Metadata">
      <EmptyState
        description="Case metadata, evidence hashes, chain-of-custody fields, and source attributes will appear here when connected."
        icon={<Fingerprint aria-hidden="true" size={19} />}
        title="Metadata unavailable"
      />
      <div className="border-t border-border px-4 py-3">
        <p className="flex items-center gap-2 text-[11px] text-subtle">
          <Database aria-hidden="true" size={13} />
          No persistence record loaded
        </p>
      </div>
    </Panel>
  );
}

