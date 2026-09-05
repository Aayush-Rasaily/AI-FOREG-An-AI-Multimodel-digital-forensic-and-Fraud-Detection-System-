import { useState } from "react";
import { ClipboardCheck } from "lucide-react";

import {
  useCaseReviewHistoryQuery,
  useCaseReviewQuery,
  useCreateApprovalMutation,
  useGenerateCaseReviewMutation,
  useUpdateChecklistItemMutation,
} from "../../hooks/useCaseReview";
import { ApiClientError } from "../../services/api/client";
import { ApprovalPanel } from "./ApprovalPanel";
import { ReviewHistoryPanel } from "./ReviewHistoryPanel";
import { ReviewMetricsPanel } from "./ReviewMetricsPanel";
import { ValidationChecklist } from "./ValidationChecklist";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { Select } from "../ui/Select";

interface CaseReviewPanelProps {
  caseId: string;
}

export function CaseReviewPanel({ caseId }: CaseReviewPanelProps) {
  const query = useCaseReviewQuery(caseId);
  const generateMutation = useGenerateCaseReviewMutation(caseId);
  const historyQuery = useCaseReviewHistoryQuery(caseId);
  const updateItemMutation = useUpdateChecklistItemMutation(caseId);
  const approvalMutation = useCreateApprovalMutation(caseId);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const isNotFound =
    query.error instanceof ApiClientError && query.error.status === 404;
  const run = query.data?.data;
  const history = historyQuery.data?.data?.items ?? [];

  return (
    <div className="space-y-4">
      <Panel
        description="Deterministic evidence validation, checklists, and multi-role approvals from existing investigation outputs — without re-running AI or automating legal decisions."
        title="Case Review"
      >
        <div className="space-y-4 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              {run ? (
                <>
                  <Badge tone="cyan">{run.status}</Badge>
                  <Badge tone="neutral">{run.stage}</Badge>
                  <Badge tone="neutral">
                    {(run.metrics.validation_pct * 100).toFixed(0)}% validated
                  </Badge>
                  <Badge tone="amber">
                    {run.metrics.outstanding_issues} outstanding
                  </Badge>
                  <Badge tone="red">
                    {run.metrics.blocking_issues} blocking
                  </Badge>
                </>
              ) : (
                <Badge tone="neutral">Not reviewed</Badge>
              )}
            </div>
            <Button
              disabled={generateMutation.isPending}
              onClick={() => generateMutation.mutate()}
              size="sm"
            >
              <ClipboardCheck size={14} /> Start review
            </Button>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <label className="block text-xs text-slate-400">
              Search
              <Input
                className="mt-1 w-56"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Checklist item or notes"
                value={search}
              />
            </label>
            <label className="block text-xs text-slate-400">
              Status
              <Select
                className="mt-1 w-44"
                onChange={(event) => setStatusFilter(event.target.value)}
                value={statusFilter}
              >
                <option value="all">All statuses</option>
                {(
                  ["PENDING", "PASS", "FAIL", "NA", "BLOCKED"] as const
                ).map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </Select>
            </label>
          </div>

          {query.isLoading ? (
            <LoadingState label="Loading case review" />
          ) : null}
          {query.isError && !isNotFound ? (
            <ErrorState
              description="Unable to load case review."
              title="Case review unavailable"
            />
          ) : null}
          {generateMutation.isError ? (
            <ErrorState
              description="Case review generation failed."
              title="Review error"
            />
          ) : null}
          {(isNotFound || (!run && !query.isLoading)) &&
          !generateMutation.isPending ? (
            <EmptyState
              description="Start a review to build a deterministic validation checklist from existing evidence and analysis outputs."
              title="No case review"
            />
          ) : null}

          {run?.provenance ? (
            <div className="text-[11px] text-slate-600">
              Provenance · engine {String(run.engine_version)} · policy{" "}
              {String(run.policy_version)} · sources{" "}
              {Array.isArray(run.provenance.sources)
                ? (run.provenance.sources as string[]).join(", ")
                : "—"}
            </div>
          ) : null}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <ReviewMetricsPanel
          blocking={run?.blocking ?? []}
          metrics={run?.metrics ?? null}
          outstanding={run?.outstanding ?? []}
          stage={run?.stage ?? null}
        />
        <ApprovalPanel
          approvals={run?.approvals ?? []}
          onSubmit={(payload) =>
            approvalMutation.mutate({
              ...payload,
              run_id: run?.id ?? undefined,
            })
          }
          requiredRoles={run?.required_roles ?? []}
          submitting={approvalMutation.isPending}
        />
        <ValidationChecklist
          items={run?.checklist ?? []}
          onMarkPass={(itemId) =>
            updateItemMutation.mutate({
              itemId,
              status: "PASS",
              reviewer: "investigator",
            })
          }
          search={search}
          statusFilter={statusFilter}
        />
        <ReviewHistoryPanel items={history} />
      </div>
    </div>
  );
}
