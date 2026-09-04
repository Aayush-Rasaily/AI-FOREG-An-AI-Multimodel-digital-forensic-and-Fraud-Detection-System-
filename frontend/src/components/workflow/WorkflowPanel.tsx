import {
  useInvestigationWorkflowQuery,
  useWorkflowStatusMutation,
} from "../../hooks/useWorkflow";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { WorkflowStatusBadge } from "./WorkflowStatusBadge";

export function WorkflowPanel({ caseId }: { caseId: string }) {
  const query = useInvestigationWorkflowQuery(caseId);
  const transition = useWorkflowStatusMutation(caseId);
  const workflow = query.data?.data;

  return (
    <Panel
      description="Deterministic investigation lifecycle (Phase 8E)."
      title="Investigation Workflow"
    >
      <div className="space-y-3 p-4">
        {query.isLoading && <LoadingState label="Loading workflow" />}
        {query.isError && (
          <ErrorState
            description="Investigation workflow could not be loaded."
            title="Error"
          />
        )}
        {workflow && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <WorkflowStatusBadge status={workflow.status} />
              <span className="text-[11px] text-slate-500">
                policy {workflow.policy_version}
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {workflow.allowed_transitions.map((status) => (
                <Button
                  key={status}
                  disabled={transition.isPending}
                  onClick={() => void transition.mutateAsync(status)}
                  size="sm"
                  variant="secondary"
                >
                  Advance to {status.replaceAll("_", " ")}
                </Button>
              ))}
              {workflow.allowed_transitions.length === 0 && (
                <p className="text-xs text-slate-500">
                  No further transitions are allowed from this status.
                </p>
              )}
            </div>
            {workflow.activity.length > 0 && (
              <div className="space-y-2 border-t border-slate-800 pt-3">
                <h3 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                  Workflow activity
                </h3>
                <ul className="max-h-48 space-y-1 overflow-y-auto text-xs text-slate-400">
                  {workflow.activity.map((event, index) => (
                    <li key={`${event.timestamp}-${index}`}>
                      <span className="text-slate-300">{event.summary}</span>
                      <span className="ml-2 text-slate-600">
                        {event.timestamp}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </Panel>
  );
}
