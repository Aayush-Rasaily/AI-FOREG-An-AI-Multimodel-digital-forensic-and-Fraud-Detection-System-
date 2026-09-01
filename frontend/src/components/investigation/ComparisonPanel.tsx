import { useState } from "react";
import { GitCompare, ShieldCheck } from "lucide-react";

import {
  useCaseReferencesQuery,
  useCompareEvidenceMutation,
  useEvidenceComparisonSummaryQuery,
  useEvidenceComparisonsQuery,
  useRegisterReferenceMutation,
} from "../../hooks/useComparison";
import type { EvidenceRecord } from "../../types/evidence";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { Select } from "../ui/Select";

interface ComparisonPanelProps {
  evidence?: EvidenceRecord;
}

const statusTone: Record<
  string,
  "neutral" | "cyan" | "green" | "amber" | "red"
> = {
  SUCCEEDED: "green",
  RUNNING: "cyan",
  QUEUED: "amber",
  FAILED: "red",
};

export function ComparisonPanel({ evidence }: ComparisonPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const caseId = evidence?.case_id ?? "";
  const enabled = Boolean(evidenceId && caseId);
  const [selectedReferenceId, setSelectedReferenceId] = useState("");
  const [referenceLabel, setReferenceLabel] = useState("");
  const referencesQuery = useCaseReferencesQuery(caseId);
  const summaryQuery = useEvidenceComparisonSummaryQuery(evidenceId);
  const comparisonsQuery = useEvidenceComparisonsQuery(evidenceId);
  const compareMutation = useCompareEvidenceMutation(evidenceId);
  const registerMutation = useRegisterReferenceMutation(caseId);
  const summary = summaryQuery.data?.data;
  const status = summary?.status ?? "QUEUED";
  const references = referencesQuery.data?.data.items ?? [];

  if (!enabled) {
    return (
      <Panel title="Reference comparison">
        <div className="p-4">
          <EmptyState
            className="min-h-48 rounded-lg border border-dashed border-slate-800"
            description="Select evidence to compare against trusted reference material."
            icon={<GitCompare aria-hidden="true" size={19} />}
            title="No evidence selected"
          />
        </div>
      </Panel>
    );
  }

  return (
    <Panel title="Reference comparison">
      <div className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge tone={statusTone[status] ?? "neutral"}>{status}</Badge>
            {summary && summary.differences_count > 0 && (
              <span className="text-[11px] text-slate-500">
                {summary.differences_count} differences
              </span>
            )}
          </div>
        </div>

        <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto]">
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
                evidence_id: evidenceId,
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
        {comparisonsQuery.isError && (
          <ErrorState
            description="Comparison history could not be loaded."
            onRetry={() => void comparisonsQuery.refetch()}
          />
        )}
        {compareMutation.isError && (
          <p className="mt-2 text-[11px] text-red-300">
            {compareMutation.error instanceof ApiClientError
              ? compareMutation.error.message
              : "Comparison could not be started."}
          </p>
        )}

        {comparisonsQuery.isSuccess && comparisonsQuery.data.data.items.length > 0 && (
          <div className="mt-3 space-y-2 border-t border-slate-800 pt-3">
            {comparisonsQuery.data.data.items.map((run) => (
              <div
                className="rounded border border-slate-800 px-2.5 py-2 text-xs text-slate-400"
                key={run.id}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={statusTone[run.status] ?? "neutral"}>
                    {run.status}
                  </Badge>
                  <span>{run.differences_count} differences</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Panel>
  );
}
