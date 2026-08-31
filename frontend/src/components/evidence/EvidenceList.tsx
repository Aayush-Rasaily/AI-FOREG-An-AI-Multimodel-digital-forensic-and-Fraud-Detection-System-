import { FileArchive } from "lucide-react";

import type { EvidenceRecord } from "../../types/evidence";
import { EvidenceCard } from "./EvidenceCard";
import { EmptyState } from "../ui/EmptyState";
import { EvidenceProcessingPanel } from "./EvidenceProcessingPanel";

interface EvidenceListProps {
  items: EvidenceRecord[];
}

function evidenceKind(item: EvidenceRecord): "image" | "pdf" | "video" | "audio" | "document" {
  if (item.mime_type.startsWith("image/")) return "image";
  if (item.mime_type === "application/pdf") return "pdf";
  if (item.mime_type.startsWith("video/")) return "video";
  if (item.mime_type.startsWith("audio/")) return "audio";
  return "document";
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function EvidenceList({ items }: EvidenceListProps) {
  if (items.length === 0) {
    return (
      <EmptyState
        description="Register an original file to create the first immutable evidence record."
        icon={<FileArchive aria-hidden="true" size={20} />}
        title="No evidence registered"
      />
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id}>
          <EvidenceCard
            kind={evidenceKind(item)}
            meta={`${item.evidence_number} · ${formatBytes(item.file_size)} · ${item.status}`}
            name={item.original_filename}
          />
          <p className="mt-1 break-all px-3 font-mono text-[10px] text-slate-600">
            SHA-256: {item.sha256_hash}
          </p>
          <EvidenceProcessingPanel evidence={item} />
        </div>
      ))}
    </div>
  );
}
