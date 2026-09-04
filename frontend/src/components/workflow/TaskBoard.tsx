import { type FormEvent, useState } from "react";

import {
  useCreateWorkflowTaskMutation,
  useUpdateWorkflowTaskMutation,
  useWorkflowTasksQuery,
} from "../../hooks/useWorkflow";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function TaskBoard({ caseId }: { caseId: string }) {
  const query = useWorkflowTasksQuery(caseId);
  const createTask = useCreateWorkflowTaskMutation(caseId);
  const updateTask = useUpdateWorkflowTaskMutation(caseId);
  const [title, setTitle] = useState("");
  const items = query.data?.data.items ?? [];

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    await createTask.mutateAsync({
      title: title.trim(),
      task_type: "GENERAL",
    });
    setTitle("");
  }

  return (
    <Panel
      description="Investigation workflow tasks with audited lifecycle."
      title="Workflow Tasks"
    >
      <div className="space-y-3 p-4">
        <form className="flex gap-2" onSubmit={(event) => void onCreate(event)}>
          <Input
            onChange={(event) => setTitle(event.target.value)}
            placeholder="New workflow task"
            value={title}
          />
          <Button disabled={createTask.isPending} size="sm" type="submit">
            Add
          </Button>
        </form>
        {query.isLoading && <LoadingState label="Loading tasks" />}
        {query.isError && (
          <ErrorState description="Tasks could not be loaded." title="Error" />
        )}
        {!query.isLoading && !query.isError && items.length === 0 && (
          <EmptyState
            description="Create a task to track investigation work."
            title="No workflow tasks"
          />
        )}
        <ul className="space-y-2">
          {items.map((task) => (
            <li
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-800 px-3 py-2"
              key={task.id}
            >
              <div>
                <p className="text-sm text-slate-200">{task.title}</p>
                <p className="text-[11px] text-slate-500">{task.task_type}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone="cyan">{task.status}</Badge>
                {task.status !== "COMPLETED" && task.status !== "CANCELLED" && (
                  <Button
                    onClick={() =>
                      void updateTask.mutateAsync({
                        taskId: task.id,
                        action: "complete",
                      })
                    }
                    size="sm"
                    variant="secondary"
                  >
                    Complete
                  </Button>
                )}
                {task.status === "COMPLETED" && (
                  <Button
                    onClick={() =>
                      void updateTask.mutateAsync({
                        taskId: task.id,
                        action: "reopen",
                      })
                    }
                    size="sm"
                    variant="secondary"
                  >
                    Reopen
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
