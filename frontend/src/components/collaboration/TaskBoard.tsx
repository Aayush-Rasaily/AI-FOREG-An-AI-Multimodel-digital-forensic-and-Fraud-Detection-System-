import { type FormEvent, useState } from "react";

import {
  useCaseTasksQuery,
  useCreateTaskMutation,
  useUpdateTaskMutation,
} from "../../hooks/useCollaboration";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function TaskBoard({ caseId }: { caseId: string }) {
  const query = useCaseTasksQuery(caseId);
  const createTask = useCreateTaskMutation(caseId);
  const updateTask = useUpdateTaskMutation(caseId);
  const [title, setTitle] = useState("");
  const items = query.data?.data.items ?? [];

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    await createTask.mutateAsync({ title: title.trim(), priority: "medium" });
    setTitle("");
  }

  return (
    <Panel description="Investigation tasks for this case." title="Tasks">
      <form className="mb-3 flex gap-2" onSubmit={onCreate}>
        <Input
          onChange={(event) => setTitle(event.target.value)}
          placeholder="New task"
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
      <ul className="space-y-2">
        {items.map((task) => (
          <li
            className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-800 px-3 py-2 text-xs"
            key={task.id}
          >
            <div>
              <p className="text-slate-200">{task.title}</p>
              <div className="mt-1 flex gap-2">
                <Badge tone="neutral">{task.priority}</Badge>
                <Badge tone="cyan">{task.status}</Badge>
              </div>
            </div>
            {task.status !== "completed" && (
              <Button
                onClick={() =>
                  void updateTask.mutateAsync({
                    taskId: task.id,
                    payload: { status: "completed" },
                  })
                }
                size="sm"
                variant="secondary"
              >
                Complete
              </Button>
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
