import { useWorkflowReviewsQuery } from "../../hooks/useWorkflow";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function ReviewPanel({ caseId }: { caseId: string }) {
  const query = useWorkflowReviewsQuery(caseId);
  const items = query.data?.data.items ?? [];
  const pending = items.filter((item) =>
    ["PENDING", "NEEDS_REVIEW", "draft", "review"].includes(item.status),
  );
  const evidenceApprovals = items.filter(
    (item) =>
      item.review_kind === "evidence" &&
      ["APPROVED", "REJECTED", "PENDING", "NEEDS_REVIEW"].includes(item.status),
  );

  return (
    <Panel
      description="Evidence and report approval records with immutable history."
      title="Reviews & Approvals"
    >
      <div className="space-y-3 p-4">
        {query.isLoading && <LoadingState label="Loading reviews" />}
        {query.isError && (
          <ErrorState
            description="Reviews could not be loaded."
            title="Error"
          />
        )}
        {!query.isLoading && !query.isError && items.length === 0 && (
          <EmptyState
            description="No evidence or report reviews have been recorded."
            title="No reviews"
          />
        )}
        {pending.length > 0 && (
          <div>
            <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Pending reviews
            </h3>
            <ul className="space-y-2">
              {pending.map((review) => (
                <li
                  className="rounded-lg border border-slate-800 px-3 py-2 text-sm text-slate-300"
                  key={review.id}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span>{review.review_kind}</span>
                    <Badge tone="amber">{review.status}</Badge>
                  </div>
                  {review.comments && (
                    <p className="mt-1 text-xs text-slate-500">
                      {review.comments}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        {evidenceApprovals.length > 0 && (
          <div>
            <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Evidence approvals
            </h3>
            <ul className="space-y-2">
              {evidenceApprovals.map((review) => (
                <li
                  className="rounded-lg border border-slate-800 px-3 py-2 text-sm text-slate-300"
                  key={`ev-${review.id}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-xs text-slate-500">
                      {review.evidence_id ?? "evidence"}
                    </span>
                    <Badge
                      tone={
                        review.status === "APPROVED"
                          ? "green"
                          : review.status === "REJECTED"
                            ? "red"
                            : "amber"
                      }
                    >
                      {review.status}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Panel>
  );
}
