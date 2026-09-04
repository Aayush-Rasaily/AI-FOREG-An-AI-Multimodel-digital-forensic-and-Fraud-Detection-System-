import { useSecurityPermissionsQuery } from "../../hooks/useSecurity";
import { Badge } from "../ui/Badge";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function PermissionsPanel() {
  const query = useSecurityPermissionsQuery();
  const items = query.data?.data.items ?? [];

  return (
    <Panel
      description="Deterministic permission matrix across platform resources."
      title="Permissions"
    >
      <div className="space-y-3 p-4">
        {query.isLoading && <LoadingState label="Loading permissions" />}
        {query.isError && (
          <ErrorState
            description="Permissions could not be loaded."
            title="Error"
          />
        )}
        <ul className="max-h-96 space-y-2 overflow-y-auto">
          {items.map((item) => (
            <li
              className="rounded-lg border border-slate-800 px-3 py-2"
              key={item.code}
            >
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm text-slate-200">{item.code}</p>
                <Badge tone="cyan">{item.resource}</Badge>
              </div>
              <p className="text-xs text-slate-500">{item.description}</p>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
