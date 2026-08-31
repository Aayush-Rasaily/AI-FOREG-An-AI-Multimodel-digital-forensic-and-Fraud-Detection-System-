import { Maximize2, MousePointer2, ZoomIn, ZoomOut } from "lucide-react";

import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";
import { EvidenceLocalization } from "./EvidenceLocalization";

interface EvidenceViewerProps {
  evidenceName?: string;
}

export function EvidenceViewer({ evidenceName }: EvidenceViewerProps) {
  return (
    <Panel
      className="min-h-[30rem]"
      description="A controlled viewport for source evidence and future engine overlays."
      title={evidenceName || "Evidence viewer"}
    >
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2">
        <span className="text-[11px] text-slate-600">Source viewport / read-only</span>
        <div className="flex items-center gap-1">
          <Button aria-label="Select annotation tool" disabled size="sm" variant="ghost">
            <MousePointer2 aria-hidden="true" size={14} />
          </Button>
          <Button aria-label="Zoom out" disabled size="sm" variant="ghost">
            <ZoomOut aria-hidden="true" size={14} />
          </Button>
          <Button aria-label="Zoom in" disabled size="sm" variant="ghost">
            <ZoomIn aria-hidden="true" size={14} />
          </Button>
          <Button aria-label="Maximize viewer" disabled size="sm" variant="ghost">
            <Maximize2 aria-hidden="true" size={14} />
          </Button>
        </div>
      </div>
      <div className="space-y-4 p-4">
        <div className="rounded-lg border border-slate-800 bg-slate-950/80">
          <EmptyState
            description="Select a connected image, PDF, video, audio, document, or signature to open it here. Evidence loading is not enabled in Phase 2."
            title="No evidence loaded"
          />
        </div>
        <EvidenceLocalization />
      </div>
    </Panel>
  );
}

