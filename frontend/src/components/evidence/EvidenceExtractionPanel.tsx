import { useEffect, useState } from "react";
import { ScanSearch } from "lucide-react";

import {
  useEvidenceExtractionArtifactsQuery,
  useEvidenceExtractionsQuery,
  useEvidenceRegionsQuery,
  useExtractEvidenceMutation,
} from "../../hooks/useEvidence";
import { ApiClientError } from "../../services/api/client";
import type { EvidenceRecord, ExtractionStatus } from "../../types/evidence";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { EvidenceLocalization } from "./EvidenceLocalization";

interface EvidenceExtractionPanelProps {
  evidence: EvidenceRecord;
}

const statusTone: Record<
  ExtractionStatus,
  "neutral" | "cyan" | "green" | "amber" | "red"
> = {
  SUCCEEDED: "green",
  PARTIAL: "amber",
  UNAVAILABLE: "neutral",
  FAILED: "red",
};

export function EvidenceExtractionPanel({
  evidence,
}: EvidenceExtractionPanelProps) {
  const extractionsQuery = useEvidenceExtractionsQuery(evidence.id);
  const regionsQuery = useEvidenceRegionsQuery(evidence.id);
  const artifactsQuery = useEvidenceExtractionArtifactsQuery(evidence.id);
  const extractMutation = useExtractEvidenceMutation(evidence.id);
  const [selectedPage, setSelectedPage] = useState<number | null>(null);
  const extractionData = extractionsQuery.data?.data;
  const extractionItems = extractionData?.items ?? [];
  const pages = Array.from(
    new Set(
      extractionItems
        .map((item) => item.page_number)
        .filter((page): page is number => page !== null),
    ),
  ).sort((left, right) => left - right);
  const visibleItems =
    selectedPage === null
      ? extractionItems
      : extractionItems.filter(
          (item) =>
            item.page_number === selectedPage || item.page_number === null,
        );
  const status = extractionData?.status || "UNAVAILABLE";
  const { refetch: refetchArtifacts } = artifactsQuery;

  useEffect(() => {
    if (status === "SUCCEEDED" || status === "PARTIAL") {
      void refetchArtifacts();
    }
  }, [refetchArtifacts, status]);

  return (
    <div className="mt-2 rounded-lg border border-slate-800 bg-slate-950/50 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ScanSearch aria-hidden="true" className="text-slate-500" size={14} />
          <span className="text-[11px] uppercase tracking-wider text-slate-600">
            Extraction
          </span>
          <Badge tone={statusTone[status]}>{status}</Badge>
        </div>
        <Button
          disabled={
            extractMutation.isPending ||
            extractionData?.status === "UNAVAILABLE" &&
              extractionData.error_code === "EXTRACTION_IN_PROGRESS"
          }
          onClick={() => extractMutation.mutate()}
          size="sm"
          variant="secondary"
        >
          {extractMutation.isPending ? "Extracting" : "Extract evidence"}
        </Button>
      </div>

      {extractionsQuery.isPending && <LoadingState label="Loading extractions" />}
      {extractionsQuery.isError && (
        <ErrorState
          description="Extraction records could not be loaded."
          onRetry={() => void extractionsQuery.refetch()}
        />
      )}
      {extractMutation.isError && (
        <p className="mt-2 text-[11px] text-red-300">
          {extractMutation.error instanceof ApiClientError
            ? extractMutation.error.message
            : "Extraction could not be started."}
        </p>
      )}
      {extractionData?.error_code &&
        extractionData.error_code !== "EXTRACTION_NOT_RUN" && (
          <p className="mt-2 text-[11px] text-amber-300">
            Capability status: {extractionData.error_code}
          </p>
        )}

      {regionsQuery.isSuccess && (
        <div className="mt-3">
          <p className="mb-2 text-[11px] uppercase tracking-wider text-slate-600">
            Localization
          </p>
          <EvidenceLocalization regions={regionsQuery.data.data.items} />
        </div>
      )}
      {regionsQuery.isError && (
        <p className="mt-2 text-[11px] text-red-300">
          Localized regions could not be loaded.
        </p>
      )}

      <div className="mt-3 border-t border-slate-800 pt-3">
        <p className="text-[11px] uppercase tracking-wider text-slate-600">
          Structured evidence
        </p>
        {pages.length > 0 && (
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-[10px] text-slate-600">Pages</span>
            <Button
              aria-pressed={selectedPage === null}
              onClick={() => setSelectedPage(null)}
              size="sm"
              variant={selectedPage === null ? "secondary" : "ghost"}
            >
              All
            </Button>
            {pages.map((page) => (
              <Button
                aria-label={`Select page ${page}`}
                aria-pressed={selectedPage === page}
                key={page}
                onClick={() => setSelectedPage(page)}
                size="sm"
                variant={selectedPage === page ? "secondary" : "ghost"}
              >
                {page}
              </Button>
            ))}
          </div>
        )}
        {extractionsQuery.isSuccess && extractionItems.length === 0 && (
            <EmptyState
              description="No extracted text, pages, regions, or stream information is available."
              title="No extraction records"
            />
          )}
        {extractionsQuery.isSuccess && visibleItems.length > 0 && (
          <div className="mt-2 max-h-64 space-y-2 overflow-y-auto">
            {visibleItems.map((item) => (
              <div
                className="rounded border border-slate-800 px-2.5 py-2"
                key={item.id}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="purple">{item.extraction_type}</Badge>
                  {item.page_number && (
                    <span className="text-[10px] text-slate-500">
                      Page {item.page_number}
                    </span>
                  )}
                  {item.frame_number !== null && (
                    <span className="text-[10px] text-slate-500">
                      Frame {item.frame_number}
                    </span>
                  )}
                  {item.confidence !== null && (
                    <span className="text-[10px] text-slate-500">
                      Confidence {(item.confidence * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                {item.content && (
                  <p className="mt-1 whitespace-pre-wrap break-words text-xs text-slate-300">
                    {item.content}
                  </p>
                )}
                {(item.extraction_type === "AUDIO_STREAM" ||
                  item.extraction_type === "METADATA") &&
                  Object.keys(item.metadata).length > 0 && (
                    <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-[10px] text-slate-500">
                      {Object.entries(item.metadata)
                        .filter(([, value]) => typeof value !== "object")
                        .slice(0, 8)
                        .map(([key, value]) => (
                          <span key={key}>
                            {key}: {String(value)}
                          </span>
                        ))}
                    </div>
                  )}
                <p className="mt-1 text-[10px] text-slate-600">
                  {item.method} v{item.version} · {item.source_type}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-3 border-t border-slate-800 pt-3">
        <p className="text-[11px] uppercase tracking-wider text-slate-600">
          Extraction artifacts
        </p>
        {artifactsQuery.isError && (
          <p className="mt-2 text-[11px] text-red-300">
            Extraction artifacts could not be loaded.
          </p>
        )}
        {artifactsQuery.isSuccess &&
          (artifactsQuery.data.data.items.length === 0 ? (
            <EmptyState
              description="Structured extraction artifacts will appear after extraction."
              title="No extraction artifacts"
            />
          ) : (
            <div className="mt-2 flex flex-wrap gap-2">
              {artifactsQuery.data.data.items.map((artifact) => (
                <Badge key={artifact.id} tone="neutral">
                  {artifact.artifact_type} · {artifact.file_size} bytes
                </Badge>
              ))}
            </div>
          ))}
      </div>
    </div>
  );
}
