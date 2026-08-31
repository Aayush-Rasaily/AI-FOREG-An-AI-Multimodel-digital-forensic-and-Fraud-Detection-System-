import { FileArchive } from "lucide-react";

import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

export function EvidenceNavigator() {
  return (
    <Panel
      className="min-h-[30rem]"
      description="Case-linked source material"
      title="Evidence navigator"
    >
      <EmptyState
        className="min-h-[25rem]"
        description="Evidence will be listed here with type, hash, custody status, and source metadata after the evidence service is connected."
        icon={<FileArchive aria-hidden="true" size={19} />}
        title="No evidence linked"
      />
    </Panel>
  );
}

