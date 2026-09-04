import { useWorkflowNotificationsQuery } from "../../hooks/useWorkflow";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function NotificationsPanel({ caseId }: { caseId: string }) {
  const query = useWorkflowNotificationsQuery(caseId);
  const items = query.data?.data.items ?? [];

  return (
    <Panel
      description="Deterministic in-app workflow notifications."
      title="Workflow Notifications"
    >
      <div className="space-y-3 p-4">
        {query.isLoading && <LoadingState label="Loading notifications" />}
        {query.isError && (
          <ErrorState
            description="Notifications could not be loaded."
            title="Error"
          />
        )}
        {!query.isLoading && !query.isError && items.length === 0 && (
          <EmptyState
            description="Assignment and approval events appear here."
            title="No notifications"
          />
        )}
        <ul className="space-y-2">
          {items.map((item) => (
            <li
              className="rounded-lg border border-slate-800 px-3 py-2"
              key={item.id}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm text-slate-200">{item.title}</p>
                <Badge tone={item.status === "unread" ? "amber" : "neutral"}>
                  {item.kind}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-slate-500">{item.body}</p>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
