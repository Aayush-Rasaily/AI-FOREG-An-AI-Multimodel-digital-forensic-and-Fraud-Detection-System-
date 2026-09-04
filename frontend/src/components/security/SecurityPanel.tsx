import { useSecurityRolesQuery } from "../../hooks/useSecurity";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function SecurityPanel() {
  const query = useSecurityRolesQuery();
  const items = query.data?.data.items ?? [];

  return (
    <Panel
      description="Enterprise governance roles (SECURITY_POLICY_VERSION 1.0)."
      title="Security Governance"
    >
      <div className="space-y-3 p-4">
        {query.isLoading && <LoadingState label="Loading security roles" />}
        {query.isError && (
          <ErrorState
            description="Security roles could not be loaded."
            title="Error"
          />
        )}
        <ul className="space-y-2">
          {items.map((role) => (
            <li
              className="rounded-lg border border-slate-800 px-3 py-2"
              key={role.code}
            >
              <p className="text-sm text-slate-200">{role.name}</p>
              <p className="text-xs text-slate-500">{role.description}</p>
              <p className="mt-1 text-[11px] text-slate-600">
                {role.permissions.length} permissions
              </p>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
