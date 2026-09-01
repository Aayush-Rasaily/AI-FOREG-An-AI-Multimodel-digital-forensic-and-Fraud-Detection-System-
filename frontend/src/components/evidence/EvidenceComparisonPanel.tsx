import { useState } from "react";
import { GitCompare, ShieldCheck } from "lucide-react";

import {
  useCaseReferencesQuery,
  useCompareEvidenceMutation,
  useEvidenceComparisonSummaryQuery,
  useEvidenceComparisonsQuery,
  useEvidenceDifferencesQuery,
  useRegisterReferenceMutation,
} from "../../hooks/useComparison";
import { ApiClientError } from "../../services/api/client";
import type { EvidenceRecord } from "../../types/evidence";
import type { Difference } from "../../types/comparison";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { Select } from "../ui/Select";

interface EvidenceComparisonPanelProps {
  evidence: EvidenceRecord;
}

const severityTone: Record<string, "neutral" | "cyan" | "green" | "amber" | "red"> =
  {
    INFO: "neutral",
    LOW: "cyan",
    MEDIUM: "amber",
    HIGH: "red",
    CRITICAL: "red",
  };

export function EvidenceComparisonPanel({ evidence }: EvidenceComparisonPanelProps) {
  const [selectedReferenceId, setSelectedReferenceId] = useState("");
  const [referenceLabel, setReferenceLabel] = useState("");
  const [activeDifferenceIndex, setActiveDifferenceIndex] = useState(0);
  const referencesQuery = useCaseReferencesQuery(evidence.case_id);
  const summaryQuery = useEvidenceComparisonSummaryQuery(evidence.id);
  const comparisonsQuery = useEvidenceComparisonsQuery(evidence.id);
  const differencesQuery = useEvidenceDifferencesQuery(evidence.id);
  const compareMutation = useCompareEvidenceMutation(evidence.id);
  const registerMutation = useRegisterReferenceMutation(evidence.case_id);
  const summary = summaryQuery.data?.data;
  const differences = differencesQuery.data?.data.items ?? [];
  const references = referencesQuery.data?.data.items ?? [];
  const status = summary?.status ?? "QUEUED";
  const activeDifference: Difference | undefined =
    differences[activeDifferenceIndex];

  return (
    <div className="mt-2 rounded-lg border border-slate-800 bg-slate-950/50 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <GitCompare aria-hidden="true" className="text-slate-500" size={14} />
          <span className="text-[11px] uppercase tracking-wider text-slate-600">
            Reference comparison
          </span>
          <Badge tone={status === "SUCCEEDED" ? "green" : status === "FAILED" ? "red" : "neutral"}>
            {status}
          </Badge>
        </div>
      </div>

      <div className="mt-3 grid gap-2 border-t border-slate-800 pt-3 sm:grid-cols-[1fr_auto]">
        <Select
          aria-label="Select reference evidence"
          onChange={(event) => setSelectedReferenceId(event.target.value)}
          value={selectedReferenceId}
        >
          <option value="">Select trusted reference</option>
          {references.map((reference) => (
            <option key={reference.id} value={reference.id}>
              {reference.label} · {reference.original_filename}
            </option>
          ))}
        </Select>
        <Button
          disabled={
            !selectedReferenceId ||
            compareMutation.isPending ||
            status === "RUNNING"
          }
          onClick={() => compareMutation.mutate(selectedReferenceId)}
          size="sm"
          variant="secondary"
        >
          {compareMutation.isPending ? "Comparing" : "Compare"}
        </Button>
      </div>

      <div className="mt-2 flex flex-wrap items-end gap-2">
        <label className="min-w-0 flex-1">
          <span className="mb-1 block text-[10px] uppercase tracking-wider text-slate-600">
            Register as reference
          </span>
          <Input
            onChange={(event) => setReferenceLabel(event.target.value)}
            placeholder="Reference label"
            value={referenceLabel}
          />
        </label>
        <Button
          disabled={!referenceLabel.trim() || registerMutation.isPending}
          onClick={() =>
            registerMutation.mutate({
              evidence_id: evidence.id,
              label: referenceLabel.trim(),
            })
          }
          size="sm"
          variant="ghost"
        >
          <ShieldCheck aria-hidden="true" className="mr-1" size={14} />
          Register
        </Button>
      </div>

      {(summaryQuery.isPending || referencesQuery.isPending) && (
        <LoadingState label="Loading comparison data" />
      )}

      {compareMutation.isError && (
        <p className="mt-2 text-[11px] text-red-300">
          {compareMutation.error instanceof ApiClientError
            ? compareMutation.error.message
            : "Comparison could not be started."}
        </p>
      )}

      {comparisonsQuery.isSuccess && comparisonsQuery.data.data.items.length > 0 && (
        <div className="mt-3 border-t border-slate-800 pt-2">
          <p className="text-[10px] uppercase tracking-wider text-slate-600">
            Comparison history
          </p>
          <div className="mt-1 flex flex-wrap gap-1">
            {comparisonsQuery.data.data.items.slice(0, 4).map((run) => (
              <Badge key={run.id} tone={run.status === "SUCCEEDED" ? "green" : "neutral"}>
                {run.differences_count} diff · {run.status}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {differencesQuery.isSuccess && differences.length === 0 && status === "SUCCEEDED" && (
        <EmptyState
          className="mt-2 min-h-24"
          description="Comparison completed without localized differences."
          title="No differences"
        />
      )}

      {differences.length > 0 && (
        <div className="mt-3 space-y-2 border-t border-slate-800 pt-2">
          <p className="text-[10px] uppercase tracking-wider text-slate-600">
            Differences ({differences.length})
          </p>
          <div className="max-h-40 space-y-1 overflow-y-auto">
            {differences.slice(0, 12).map((difference, index) => (
              <button
                className={`w-full rounded border px-2 py-1.5 text-left transition-colors ${
                  index === activeDifferenceIndex
                    ? "border-cyan-400/40 bg-cyan-400/10"
                    : "border-slate-800 hover:border-slate-700"
                }`}
                key={difference.id}
                onClick={() => setActiveDifferenceIndex(index)}
                type="button"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={severityTone[difference.severity] ?? "neutral"}>
                    {difference.severity}
                  </Badge>
                  <span className="text-[10px] text-slate-400">
                    {difference.difference_type}
                  </span>
                </div>
                <p className="mt-0.5 text-[11px] text-slate-400">
                  {difference.description}
                </p>
              </button>
            ))}
          </div>

          {activeDifference && (
            <div className="grid gap-2 rounded border border-slate-800 p-2 sm:grid-cols-2">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-600">
                  Original
                </p>
                <p className="mt-1 text-[11px] text-slate-300">
                  {activeDifference.original_value ?? "—"}
                </p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-600">
                  Submitted
                </p>
                <p className="mt-1 text-[11px] text-slate-300">
                  {activeDifference.submitted_value ?? "—"}
                </p>
              </div>
              {activeDifference.regions[0] && (
                <div className="sm:col-span-2">
                  <p className="text-[10px] uppercase tracking-wider text-slate-600">
                    Localization
                  </p>
                  <p className="mt-1 font-mono text-[10px] text-slate-500">
                    page={activeDifference.regions[0].page_number ?? "—"} · x=
                    {activeDifference.regions[0].x.toFixed(1)} y=
                    {activeDifference.regions[0].y.toFixed(1)} · conf=
                    {(activeDifference.confidence * 100).toFixed(0)}%
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
