import { PageHeader } from "../components/layout/PageHeader";
import { PermissionsPanel } from "../components/security/PermissionsPanel";
import { PolicyViolationsPanel } from "../components/security/PolicyViolationsPanel";
import { SecurityPanel } from "../components/security/SecurityPanel";
import { useSecurityPolicyQuery } from "../hooks/useSecurity";
import { Badge } from "../components/ui/Badge";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { Panel } from "../components/ui/Panel";

export function SecurityGovernancePage() {
  const policyQuery = useSecurityPolicyQuery();
  const policy = policyQuery.data?.data;

  return (
    <div>
      <PageHeader
        description="Enterprise RBAC catalog, governance policies, and violations."
        eyebrow="Administration"
        title="Security & Governance"
      />
      <div className="space-y-4">
        <Panel description="Active security policy document." title="Policy">
          <div className="space-y-2 p-4">
            {policyQuery.isLoading && (
              <LoadingState label="Loading policy" />
            )}
            {policyQuery.isError && (
              <ErrorState
                description="Security policy could not be loaded."
                title="Error"
              />
            )}
            {policy && (
              <>
                <div className="flex flex-wrap gap-2">
                  <Badge tone="cyan">
                    policy {policy.policy_version}
                  </Badge>
                  <Badge tone="neutral">
                    engine {policy.engine_version}
                  </Badge>
                </div>
                <ul className="space-y-1 text-xs text-slate-500">
                  {policy.policies.map((item) => (
                    <li key={item.code}>
                      <span className="text-slate-300">{item.code}</span>
                      {" — "}
                      {item.description}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </Panel>
        <div className="grid gap-4 xl:grid-cols-2">
          <SecurityPanel />
          <PermissionsPanel />
        </div>
        <PolicyViolationsPanel />
      </div>
    </div>
  );
}
