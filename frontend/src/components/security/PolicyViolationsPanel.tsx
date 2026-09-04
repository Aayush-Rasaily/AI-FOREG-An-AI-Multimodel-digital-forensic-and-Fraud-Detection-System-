import { useSecurityViolationsQuery } from "../../hooks/useSecurity";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function PolicyViolationsPanel({ caseId }: { caseId?: string }) {
  const query = useSecurityViolationsQuery(caseId);
  const items = query.data?.data.items ?? [];

  return (
    <Panel
      description="Recorded governance policy violations."
      title="Policy Violations"
    >
      <div className="space-y-3 p-4">
        {query.isLoading && <LoadingState label="Loading violations" />}
        {query.isError && (
          <ErrorState
            description="Violations could not be loaded."
            title="Error"
          />
        )}
        {!query.isLoading && !query.isError && items.length === 0 && (
          <EmptyState
            description="No policy violations have been recorded."
            title="No violations"
          />
        )}
        <ul className="space-y-2">
          {items.map((item) => (
            <li
              className="rounded-lg border border-slate-800 px-3 py-2"
              key={item.id}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm text-slate-200">{item.policy_code}</p>
                <Badge
                  tone={
                    item.severity === "CRITICAL" || item.severity === "HIGH"
                      ? "red"
                      : "amber"
                  }
                >
                  {item.severity}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-slate-500">{item.message}</p>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
