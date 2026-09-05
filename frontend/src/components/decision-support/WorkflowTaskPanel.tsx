import type { WorkflowTask } from "../../types/decisionSupport";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

interface WorkflowTaskPanelProps {
  tasks: WorkflowTask[];
  search: string;
  stageFilter: string;
  onComplete?: (taskId: string) => void;
}

export function WorkflowTaskPanel({
  tasks,
  search,
  stageFilter,
  onComplete,
}: WorkflowTaskPanelProps) {
  const query = search.trim().toLowerCase();
  const visible = tasks.filter((item) => {
    const matchesStage =
      stageFilter === "all" || item.stage === stageFilter;
    const matchesSearch =
      query.length === 0 ||
      item.title.toLowerCase().includes(query) ||
      item.task_type.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query);
    return matchesStage && matchesSearch;
  });

  return (
    <Panel description="Deterministic investigator tasks by stage." title="Task board">
      <div className="space-y-3 p-4">
        {!visible.length ? (
          <EmptyState
            description="No tasks match the current filters."
            title="No tasks"
          />
        ) : (
          visible.map((item) => (
            <div
              className="rounded-lg border border-slate-800 p-3 text-xs text-slate-400"
              key={item.task_key}
            >
              <div className="mb-2 flex flex-wrap gap-2">
                <Badge tone="cyan">{item.priority}</Badge>
                <Badge tone="neutral">{item.stage}</Badge>
                <Badge tone="neutral">{item.status}</Badge>
              </div>
              <p className="text-sm text-slate-200">{item.title}</p>
              <p className="mt-1">{item.description}</p>
              <p className="mt-2 text-[11px] text-slate-600">
                Effort ~{item.estimated_effort_hours}h · Provenance engine{" "}
                {String(item.provenance.engine_version ?? "—")}
              </p>
              {item.id && onComplete && item.status !== "COMPLETED" ? (
                <button
                  className="mt-2 text-cyan-300 hover:underline"
                  onClick={() => onComplete(item.id!)}
                  type="button"
                >
                  Mark completed
                </button>
              ) : null}
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
