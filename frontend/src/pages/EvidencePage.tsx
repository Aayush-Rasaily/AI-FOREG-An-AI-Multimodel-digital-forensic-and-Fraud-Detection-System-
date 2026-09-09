import { useEffect, useMemo, useState } from "react";
import { Filter, Search } from "lucide-react";

import { EvidenceList } from "../components/evidence/EvidenceList";
import { EvidenceUploadForm } from "../components/evidence/EvidenceUploadForm";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { FilterChip } from "../components/ui/FilterChip";
import { Input } from "../components/ui/Input";
import { LoadingState } from "../components/ui/LoadingState";
import { Select } from "../components/ui/Select";
import { useCasesQuery } from "../hooks/useCases";
import { useCaseEvidenceQuery } from "../hooks/useEvidence";
import { ApiClientError } from "../services/api/client";

type KindFilter = "all" | "image" | "video" | "audio" | "document";

function matchesKind(
  mime: string,
  filter: KindFilter,
): boolean {
  if (filter === "all") return true;
  if (filter === "image") return mime.startsWith("image/");
  if (filter === "video") return mime.startsWith("video/");
  if (filter === "audio") return mime.startsWith("audio/");
  return (
    !mime.startsWith("image/") &&
    !mime.startsWith("video/") &&
    !mime.startsWith("audio/")
  );
}

export function EvidencePage() {
  const casesQuery = useCasesQuery();
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [search, setSearch] = useState("");
  const [kindFilter, setKindFilter] = useState<KindFilter>("all");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const evidenceQuery = useCaseEvidenceQuery(selectedCaseId);

  useEffect(() => {
    if (!selectedCaseId && casesQuery.data?.data.items[0]) {
      setSelectedCaseId(casesQuery.data.data.items[0].id);
    }
  }, [casesQuery.data, selectedCaseId]);

  const selectedCase = casesQuery.data?.data.items.find(
    (item) => item.id === selectedCaseId,
  );

  const filteredItems = useMemo(() => {
    const items = evidenceQuery.data?.data.items ?? [];
    const needle = search.trim().toLowerCase();
    return items.filter((item) => {
      if (!matchesKind(item.mime_type, kindFilter)) {
        return false;
      }
      if (!needle) {
        return true;
      }
      return (
        item.original_filename.toLowerCase().includes(needle) ||
        item.evidence_number.toLowerCase().includes(needle) ||
        item.sha256_hash.toLowerCase().includes(needle) ||
        (selectedCase?.case_number ?? "").toLowerCase().includes(needle)
      );
    });
  }, [evidenceQuery.data, kindFilter, search, selectedCase?.case_number]);

  return (
    <div className="min-w-0">
      <PageHeader
        description="A controlled index for evidence items, custody records, and source artifacts."
        eyebrow="Evidence registry"
        title="Evidence"
      />
      <Card className="mb-4 space-y-3 p-3 sm:p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <label className="relative min-w-0 flex-1">
            <span className="sr-only">Search evidence</span>
            <Search
              aria-hidden="true"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-subtle"
              size={16}
            />
            <Input
              className="min-h-11 pl-9"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search evidence by hash, name, or case"
              value={search}
            />
          </label>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Select
              aria-label="Select case"
              className="min-h-11 w-full sm:min-w-56"
              onChange={(event) => setSelectedCaseId(event.target.value)}
              value={selectedCaseId}
            >
              <option value="">Select a case</option>
              {(casesQuery.data?.data.items ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.case_number} · {item.title}
                </option>
              ))}
            </Select>
            <button
              aria-controls="evidence-filters"
              aria-expanded={filtersOpen}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-border px-3 text-caption text-muted hover:bg-surface-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring lg:hidden"
              onClick={() => setFiltersOpen((current) => !current)}
              type="button"
            >
              <Filter aria-hidden="true" size={16} />
              Filters
            </button>
          </div>
        </div>
        <div
          className={`flex flex-wrap gap-2 ${filtersOpen ? "flex" : "hidden lg:flex"}`}
          id="evidence-filters"
        >
          {(
            [
              ["all", "All types"],
              ["image", "Images"],
              ["video", "Video"],
              ["audio", "Audio"],
              ["document", "Documents"],
            ] as const
          ).map(([value, label]) => (
            <FilterChip
              active={kindFilter === value}
              key={value}
              onClick={() => setKindFilter(value)}
              onClear={
                kindFilter === value && value !== "all"
                  ? () => setKindFilter("all")
                  : undefined
              }
            >
              {label}
            </FilterChip>
          ))}
        </div>
      </Card>
      {casesQuery.isPending && <LoadingState label="Loading cases" />}
      {casesQuery.isError && (
        <ErrorState
          description={
            casesQuery.error instanceof ApiClientError
              ? casesQuery.error.message
              : "Cases could not be loaded."
          }
          onRetry={() => void casesQuery.refetch()}
        />
      )}
      {casesQuery.isSuccess && !selectedCase && (
        <Card>
          <EmptyState
            description="Create a case before registering original evidence."
            title="No case selected"
          />
        </Card>
      )}
      {selectedCase && (
        <>
          <Card className="overflow-hidden p-3 sm:p-4">
            {evidenceQuery.isPending && (
              <LoadingState label="Loading evidence" />
            )}
            {evidenceQuery.isError && (
              <ErrorState
                description="Evidence records could not be loaded."
                onRetry={() => void evidenceQuery.refetch()}
              />
            )}
            {evidenceQuery.isSuccess && (
              <EvidenceList items={filteredItems} layout="grid" />
            )}
          </Card>
          <div className="mt-4">
            <EvidenceUploadForm caseId={selectedCase.id} />
          </div>
        </>
      )}
    </div>
  );
}
