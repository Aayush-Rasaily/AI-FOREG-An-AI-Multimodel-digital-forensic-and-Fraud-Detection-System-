import { ScanSearch } from "lucide-react";
import { useState } from "react";

import type { ExtractionRecord } from "../../types/evidence";
import { EmptyState } from "../ui/EmptyState";

interface EvidenceLocalizationProps {
  regions?: ExtractionRecord[];
}

export function EvidenceLocalization({
  regions = [],
}: EvidenceLocalizationProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selectedRegion = regions.find((region) => region.id === selectedId);
  return (
    <div
      aria-label="Evidence localization viewport"
      className="relative flex min-h-40 items-center justify-center overflow-hidden rounded-lg border border-dashed border-slate-800 bg-slate-950/60"
    >
      <div className="absolute inset-6 border border-slate-800/70">
        <span className="absolute -left-px -top-px h-3 w-3 border-l border-t border-cyan-400/40" />
        <span className="absolute -right-px -top-px h-3 w-3 border-r border-t border-cyan-400/40" />
        <span className="absolute -bottom-px -left-px h-3 w-3 border-b border-l border-cyan-400/40" />
        <span className="absolute -bottom-px -right-px h-3 w-3 border-b border-r border-cyan-400/40" />
      </div>
      {regions.length === 0 ? (
        <EmptyState
          className="min-h-40"
          description="No detector-backed regions were returned. Coordinates are never invented."
          icon={<ScanSearch aria-hidden="true" size={19} />}
          title="No localized regions"
        />
      ) : (
        regions.map((region) => {
          const box = region.normalized_location;
          if (!box) return null;
          return (
            <button
              aria-label={`${region.extraction_type} region`}
              className="absolute border border-cyan-300/80 bg-cyan-300/10 text-[9px] text-cyan-100"
              onClick={() => setSelectedId(region.id)}
              key={region.id}
              style={{
                left: `${box.x * 100}%`,
                top: `${box.y * 100}%`,
                width: `${box.width * 100}%`,
                height: `${box.height * 100}%`,
              }}
              type="button"
            >
              {region.extraction_type}
            </button>
          );
        })
      )}
      {selectedRegion && (
        <div className="absolute bottom-2 left-2 right-2 rounded border border-slate-700 bg-slate-950/95 px-2 py-1.5 text-[10px] text-slate-300">
          <span className="text-cyan-200">
            {selectedRegion.extraction_type}
          </span>
          {" · "}
          {selectedRegion.source_identifier}
          {selectedRegion.page_number !== null &&
            ` · page ${selectedRegion.page_number}`}
        </div>
      )}
    </div>
  );
}

