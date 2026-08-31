import { ScanSearch } from "lucide-react";

import { EmptyState } from "../ui/EmptyState";

export function EvidenceLocalization() {
  return (
    <div
      aria-label="Evidence localization viewport"
      className="relative flex min-h-40 items-center justify-center overflow-hidden rounded-lg border border-dashed border-slate-800 bg-slate-950/60"
    >
      <div className="pointer-events-none absolute inset-6 border border-slate-800/70">
        <span className="absolute -left-px -top-px h-3 w-3 border-l border-t border-cyan-400/40" />
        <span className="absolute -right-px -top-px h-3 w-3 border-r border-t border-cyan-400/40" />
        <span className="absolute -bottom-px -left-px h-3 w-3 border-b border-l border-cyan-400/40" />
        <span className="absolute -bottom-px -right-px h-3 w-3 border-b border-r border-cyan-400/40" />
      </div>
      <EmptyState
        className="min-h-40"
        description="Bounding boxes, polygons, heatmaps, and annotations will render here when an engine supplies localization data."
        icon={<ScanSearch aria-hidden="true" size={19} />}
        title="Localization layer ready"
      />
    </div>
  );
}

