import {
  useCaseWorkflowQuery,
  useWorkflowTransitionMutation,
} from "../../hooks/useCollaboration";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function WorkflowPanel({ caseId }: { caseId: string }) {
  const query = useCaseWorkflowQuery(caseId);
  const transition = useWorkflowTransitionMutation(caseId);
  const workflow = query.data?.data;

  return (
    <Panel description="Deterministic case collaboration lifecycle." title="Workflow">
      {query.isLoading && <LoadingState label="Loading workflow" />}
      {query.isError && (
        <ErrorState description="Workflow could not be loaded." title="Error" />
      )}
      {workflow && (
        <div className="space-y-3">
          <Badge tone="cyan">{workflow.stage.replaceAll("_", " ")}</Badge>
          <div className="flex flex-wrap gap-2">
            {workflow.allowed_transitions.map((stage) => (
              <Button
                key={stage}
                onClick={() => void transition.mutateAsync(stage)}
                size="sm"
                variant="secondary"
              >
                Advance to {stage.replaceAll("_", " ")}
              </Button>
            ))}
          </div>
        </div>
      )}
    </Panel>
  );
}
