import { useCaseAccessQuery } from "../../hooks/useSecurity";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function CaseAccessPanel({ caseId }: { caseId: string }) {
  const query = useCaseAccessQuery(caseId);
  const items = query.data?.data.items ?? [];

  return (
    <Panel
      description="Case access grants for owners, investigators, reviewers, and auditors."
      title="Case Access"
    >
      <div className="space-y-3 p-4">
        {query.isLoading && <LoadingState label="Loading access" />}
        {query.isError && (
          <ErrorState
            description="Case access could not be loaded."
            title="Error"
          />
        )}
        {!query.isLoading && !query.isError && items.length === 0 && (
          <EmptyState
            description="No explicit access grants recorded for this case."
            title="No access records"
          />
        )}
        <ul className="space-y-2">
          {items.map((item) => (
            <li
              className="rounded-lg border border-slate-800 px-3 py-2"
              key={item.id}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="truncate text-xs text-slate-400">{item.user_id}</p>
                <Badge tone={item.active ? "green" : "neutral"}>
                  {item.access_level}
                </Badge>
              </div>
              {item.reason && (
                <p className="mt-1 text-xs text-slate-500">{item.reason}</p>
              )}
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
