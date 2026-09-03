import {
  useNotificationsQuery,
  useUpdateNotificationMutation,
} from "../../hooks/useCollaboration";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function NotificationPanel() {
  const query = useNotificationsQuery(true);
  const update = useUpdateNotificationMutation();
  const items = query.data?.data.items ?? [];
  const unread = query.data?.data.unread_count ?? 0;

  return (
    <Panel
      description={`${unread} unread collaboration notifications.`}
      title="Notifications"
    >
      {query.isLoading && <LoadingState label="Loading notifications" />}
      {query.isError && (
        <ErrorState
          description="Notifications could not be loaded."
          title="Error"
        />
      )}
      <ul className="space-y-2">
        {items.map((item) => (
          <li
            className="flex items-start justify-between gap-2 rounded-lg border border-slate-800 px-3 py-2 text-xs"
            key={item.id}
          >
            <div>
              <p className="text-slate-200">{item.title}</p>
              <p className="mt-1 text-slate-500">{item.body}</p>
            </div>
            <div className="flex flex-col items-end gap-1">
              <Badge tone={item.status === "unread" ? "amber" : "neutral"}>
                {item.status}
              </Badge>
              {item.status === "unread" && (
                <Button
                  onClick={() =>
                    void update.mutateAsync({ id: item.id, status: "read" })
                  }
                  size="sm"
                  variant="ghost"
                >
                  Mark read
                </Button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
