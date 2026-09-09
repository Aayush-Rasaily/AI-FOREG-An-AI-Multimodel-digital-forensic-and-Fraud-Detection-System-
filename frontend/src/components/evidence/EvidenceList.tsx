import { memo, useMemo, useState } from "react";
import { ArrowDownAZ, FileArchive, Filter } from "lucide-react";

import type { EvidenceRecord } from "../../types/evidence";
import { EvidenceCard } from "./EvidenceCard";
import { EmptyState } from "../ui/EmptyState";
import { Badge } from "../ui/Badge";
import { EvidenceComparisonPanel } from "./EvidenceComparisonPanel";
import { EvidenceExtractionPanel } from "./EvidenceExtractionPanel";
import { EvidenceForensicsPanel } from "./EvidenceForensicsPanel";
import { EvidenceProcessingPanel } from "./EvidenceProcessingPanel";
import { FilterChip } from "../ui/FilterChip";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { cn } from "../../lib/utils";

interface EvidenceListProps {
  items: EvidenceRecord[];
  layout?: "stack" | "grid";
  showDetails?: boolean;
  selectedId?: string;
  onSelect?: (id: string) => void;
}

function evidenceKind(
  item: EvidenceRecord,
): "image" | "pdf" | "video" | "audio" | "document" {
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

function riskTone(status: string): "success" | "warning" | "error" | "neutral" {
  if (status.includes("FAIL") || status.includes("ERROR")) return "error";
  if (status.includes("QUEUE") || status.includes("RUN")) return "warning";
  if (status.includes("SUCCEED") || status.includes("REGISTER")) return "success";
  return "neutral";
}

function EvidenceListComponent({
  items,
  layout = "stack",
  showDetails = true,
  selectedId,
  onSelect,
}: EvidenceListProps) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<"name" | "size" | "status">("name");
  const [groupByKind, setGroupByKind] = useState(false);
  const [kindFilter, setKindFilter] = useState<string>("all");

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    let next = items.filter((item) => {
      const kind = evidenceKind(item);
      if (kindFilter !== "all" && kind !== kindFilter) {
        return false;
      }
      if (!needle) {
        return true;
      }
      return (
        item.original_filename.toLowerCase().includes(needle) ||
        item.evidence_number.toLowerCase().includes(needle) ||
        item.sha256_hash.toLowerCase().includes(needle) ||
        item.status.toLowerCase().includes(needle)
      );
    });
    next = [...next].sort((a, b) => {
      if (sort === "size") {
        return b.file_size - a.file_size;
      }
      if (sort === "status") {
        return a.status.localeCompare(b.status);
      }
      return a.original_filename.localeCompare(b.original_filename);
    });
    return next;
  }, [items, kindFilter, query, sort]);

  const groups = useMemo(() => {
    if (!groupByKind) {
      return [{ key: "all", label: "Evidence", items: filtered }];
    }
    const map = new Map<string, EvidenceRecord[]>();
    for (const item of filtered) {
      const kind = evidenceKind(item);
      const list = map.get(kind) ?? [];
      list.push(item);
      map.set(kind, list);
    }
    return [...map.entries()].map(([key, groupItems]) => ({
      key,
      label: key,
      items: groupItems,
    }));
  }, [filtered, groupByKind]);

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
      <div className="space-y-2 rounded-lg border border-border bg-background/40 p-2">
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            aria-label="Filter evidence"
            className="min-h-9"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Filter by name, hash, status…"
            value={query}
          />
          <Select
            aria-label="Sort evidence"
            className="min-h-9 sm:w-40"
            onChange={(event) =>
              setSort(event.target.value as "name" | "size" | "status")
            }
            value={sort}
          >
            <option value="name">Sort: Name</option>
            <option value="size">Sort: Size</option>
            <option value="status">Sort: Status</option>
          </Select>
        </div>
        <div className="flex flex-wrap gap-2">
          {(["all", "image", "pdf", "video", "audio", "document"] as const).map(
            (kind) => (
              <FilterChip
                active={kindFilter === kind}
                key={kind}
                onClick={() => setKindFilter(kind)}
              >
                {kind}
              </FilterChip>
            ),
          )}
          <FilterChip
            active={groupByKind}
            onClick={() => setGroupByKind((current) => !current)}
          >
            <Filter size={12} /> Group
          </FilterChip>
          <span className="inline-flex items-center gap-1 text-micro text-subtle">
            <ArrowDownAZ size={12} /> {filtered.length} shown
          </span>
        </div>
      </div>

      {groups.map((group) => (
        <div key={group.key}>
          {groupByKind && (
            <p className="mb-2 sticky top-0 z-[1] bg-surface/95 px-1 py-1 text-micro font-semibold uppercase tracking-wider text-subtle backdrop-blur">
              {group.label}
            </p>
          )}
          <div
            className={cn(
              layout === "grid"
                ? "grid gap-3 sm:grid-cols-2 desktop:grid-cols-3"
                : "space-y-3",
            )}
          >
            {group.items.map((item) => {
              const kind = evidenceKind(item);
              return (
                <article className="min-w-0" key={item.id}>
                  <EvidenceCard
                    kind={kind}
                    meta={`${item.evidence_number} · ${formatBytes(item.file_size)} · ${item.status}`}
                    name={item.original_filename}
                    onClick={
                      onSelect ? () => onSelect(item.id) : undefined
                    }
                    selected={selectedId === item.id}
                  />
                  <div className="mt-1 flex flex-wrap gap-1 px-1">
                    <Badge tone={riskTone(item.status)}>{item.status}</Badge>
                    <Badge tone="neutral">conf. n/a</Badge>
                    <Badge tone="info">{kind}</Badge>
                  </div>
                  <p className="mt-1 break-all px-1 font-mono text-[10px] text-subtle sm:px-3">
                    SHA-256: {item.sha256_hash}
                  </p>
                  {showDetails && (
                    <div className="mt-2 space-y-2">
                      <EvidenceProcessingPanel evidence={item} />
                      <EvidenceExtractionPanel evidence={item} />
                      <EvidenceForensicsPanel evidence={item} />
                      <EvidenceComparisonPanel evidence={item} />
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

export const EvidenceList = memo(EvidenceListComponent);
