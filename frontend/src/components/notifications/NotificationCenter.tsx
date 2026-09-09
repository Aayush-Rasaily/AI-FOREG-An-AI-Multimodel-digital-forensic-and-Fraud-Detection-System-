import { useProductivity } from "../../context/ProductivityContext";
import { cn } from "../../lib/utils";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Drawer } from "../ui/Drawer";

const toneBadge: Record<
  string,
  "info" | "success" | "warning" | "error" | "neutral"
> = {
  info: "info",
  success: "success",
  warning: "warning",
  error: "error",
};

export function NotificationCenter() {
  const {
    notificationOpen,
    setNotificationOpen,
    notifications,
    unreadCount,
    markAllNotificationsRead,
    clearNotifications,
  } = useProductivity();

  return (
    <Drawer
      onClose={() => setNotificationOpen(false)}
      open={notificationOpen}
      title={`Notifications${unreadCount ? ` (${unreadCount})` : ""}`}
    >
      <div className="mb-3 flex gap-2">
        <Button onClick={markAllNotificationsRead} size="sm" variant="secondary">
          Mark all read
        </Button>
        <Button onClick={clearNotifications} size="sm" variant="ghost">
          Clear
        </Button>
      </div>
      <ul className="max-h-[70vh] space-y-2 overflow-y-auto">
        {notifications.length === 0 && (
          <li className="rounded-lg border border-dashed border-border p-6 text-center text-caption text-muted">
            No notifications yet. Background jobs and processing updates appear
            here.
          </li>
        )}
        {notifications.map((item) => (
          <li
            className={cn(
              "rounded-lg border border-border p-3",
              !item.read && "bg-primary-soft/30",
            )}
            key={item.id}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-caption font-medium text-foreground">
                {item.title}
              </p>
              <Badge tone={toneBadge[item.tone] ?? "neutral"}>{item.tone}</Badge>
            </div>
            {item.description && (
              <p className="mt-1 text-caption text-muted">{item.description}</p>
            )}
            <p className="mt-2 text-micro text-subtle">
              {new Date(item.createdAt).toLocaleString()}
              {item.category ? ` · ${item.category}` : ""}
            </p>
          </li>
        ))}
      </ul>
    </Drawer>
  );
}
