import { useCaseActivityQuery } from "../../hooks/useCollaboration";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function ActivityPanel({ caseId }: { caseId: string }) {
  const query = useCaseActivityQuery(caseId);
  const items = query.data?.data.items ?? [];

  return (
    <Panel
      description="Collaborative activity for this investigation."
      title="Activity"
    >
      {query.isLoading && <LoadingState label="Loading activity" />}
      {query.isError && (
        <ErrorState description="Activity could not be loaded." title="Error" />
      )}
      <ul className="space-y-2">
        {items.map((item) => (
          <li
            className="rounded-lg border border-border px-3 py-2 text-xs text-muted"
            key={item.id}
          >
            <p className="text-foreground">{item.summary}</p>
            <p className="mt-1">
              {item.actor_username} · {item.action} ·{" "}
              {new Date(item.created_at).toLocaleString()}
            </p>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
