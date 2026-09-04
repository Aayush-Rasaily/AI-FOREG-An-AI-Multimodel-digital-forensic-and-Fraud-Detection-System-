import { useWorkflowMilestonesQuery } from "../../hooks/useWorkflow";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function MilestoneTimeline({ caseId }: { caseId: string }) {
  const query = useWorkflowMilestonesQuery(caseId);
  const items = query.data?.data.items ?? [];

  return (
    <Panel
      description="Investigation milestones, including auto-derived completion."
      title="Milestones"
    >
      <div className="space-y-3 p-4">
        {query.isLoading && <LoadingState label="Loading milestones" />}
        {query.isError && (
          <ErrorState
            description="Milestones could not be loaded."
            title="Error"
          />
        )}
        {!query.isLoading && !query.isError && items.length === 0 && (
          <EmptyState
            description="Milestones appear as the investigation progresses."
            title="No milestones yet"
          />
        )}
        <ol className="space-y-3 border-l border-slate-800 pl-4">
          {items.map((milestone) => (
            <li className="relative" key={milestone.id}>
              <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-cyan-400" />
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm text-slate-200">{milestone.label}</p>
                {milestone.auto_derived && (
                  <Badge tone="neutral">auto</Badge>
                )}
              </div>
              <p className="text-[11px] text-slate-500">
                {milestone.reached_at}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </Panel>
  );
}
