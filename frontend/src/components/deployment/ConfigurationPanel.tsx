import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { useSystemConfigurationQuery } from "../../hooks/useSystemStatus";

export function ConfigurationPanel() {
  const query = useSystemConfigurationQuery();

  if (query.isLoading) {
    return <LoadingState label="Loading configuration" />;
  }
  if (query.isError) {
    return (
      <ErrorState
        description="Unable to load configuration profile."
        title="Configuration unavailable"
      />
    );
  }

  const config = query.data?.data;
  if (!config) {
    return (
      <EmptyState
        description="No configuration profile was returned."
        title="No configuration"
      />
    );
  }

  const profile = config.profile;
  const findings = config.findings ?? [];

  return (
    <Panel
      description="Active profile summary and configuration integrity findings (no secrets)."
      title="Configuration"
    >
      <div className="space-y-4 p-4 text-sm">
        <div className="flex flex-wrap gap-2">
          <Badge tone="neutral">
            Profile: {String(profile.profile ?? "unknown")}
          </Badge>
          <Badge tone="neutral">
            Version: {String(profile.version ?? "—")}
          </Badge>
          <Badge tone={profile.debug ? "amber" : "green"}>
            Debug: {String(profile.debug ?? false)}
          </Badge>
        </div>
        <dl className="grid gap-2 text-xs text-slate-400 sm:grid-cols-2">
          <div>
            <dt className="text-slate-600">Storage backend</dt>
            <dd className="text-slate-200">
              {String(profile.storage_backend ?? "—")}
            </dd>
          </div>
          <div>
            <dt className="text-slate-600">Auth required</dt>
            <dd className="text-slate-200">
              {String(profile.auth_required ?? "—")}
            </dd>
          </div>
        </dl>
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-wide text-slate-600">
            Integrity findings
          </p>
          {findings.length ? (
            <ul className="space-y-2">
              {findings.map((item) => (
                <li
                  className="flex items-start justify-between gap-3 text-xs"
                  key={item.check}
                >
                  <div>
                    <p className="font-medium text-slate-200">{item.check}</p>
                    <p className="text-slate-500">{item.message}</p>
                  </div>
                  <Badge
                    tone={
                      item.status === "PASS"
                        ? "green"
                        : item.status === "WARN"
                          ? "amber"
                          : "red"
                    }
                  >
                    {item.status}
                  </Badge>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              description="No configuration findings were reported."
              title="No findings"
            />
          )}
        </div>
      </div>
    </Panel>
  );
}
